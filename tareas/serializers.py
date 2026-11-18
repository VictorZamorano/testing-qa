from django.contrib.auth import get_user_model
from rest_framework import serializers

from tareas.models import Tarea

# Obtenemos el modelo de usuario personalizado (si existe) o el modelo de usuario predeterminado de Django
User = get_user_model()

# Serializador para registrar nuevos usuarios con validación estricta de datos
class RegistroSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=20,
        error_messages={
            'min_length': 'La contraseña debe tener al menos 8 caracteres.',
            'max_length': 'La contraseña no puede tener más de 20 caracteres.',
        },
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')

    def validate(self, attrs):
        email = attrs.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError(
                {'email': 'Este correo electrónico ya está registrado.'}
            )
        return attrs

    @staticmethod
    def _generar_username(nombre_completo):
        base = nombre_completo.strip()[:150] or 'usuario'
        candidato = base
        contador = 1
        while User.objects.filter(username=candidato).exists():
            sufijo = f'_{contador}'
            candidato = f'{base[:150 - len(sufijo)]}{sufijo}'
            contador += 1
        return candidato

    def create(self, validated_data):
        nombre_completo = validated_data.pop('username')
        partes = nombre_completo.split(' ', 1)
        return User.objects.create_user(
            username=self._generar_username(nombre_completo),
            email=validated_data['email'],
            password=validated_data['password'],
            nombre_completo=nombre_completo,
            first_name=partes[0],
            last_name=partes[1] if len(partes) > 1 else '',
            rol='usuario',  # nunca desde el cliente
            is_active=True,
        )

# Serializador para consultar los datos del usuario autenticado sin exponer la contraseña
class UsuarioPerfilSerializer(serializers.ModelSerializer):
    """Serializador para consultar los datos del usuario autenticado sin exponer la contraseña"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'rol', 'date_joined')
        read_only_fields = ('id', 'date_joined')

# Serializador para las tareas
class TareaSerializer(serializers.ModelSerializer):
    # Datos de solo lectura del propietario. El campo "usuario" NO es
    # escribible, así que una tarea no se puede reasignar con un PATCH.
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    usuario_username = serializers.CharField(
        source='usuario.username', read_only=True
    )

    class Meta:
        model = Tarea
        fields = [
            'id', 'titulo', 'descripcion', 'completada',
            'usuario_id', 'usuario_username',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'fecha_creacion', 'fecha_actualizacion']

# Serializador para que el administrador pueda modificar roles o desactivar usuarios
class AdminUsuarioUpdateSerializer(serializers.ModelSerializer):
    """Serializador para que el administrador pueda modificar roles o desactivar usuarios"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'rol', 'is_active')
        read_only_fields = ('id', 'username', 'email')

    def validate(self, attrs):
        request = self.context.get('request')
        if not request or not self.instance:
            return attrs

        es_uno_mismo = request.user.id == self.instance.id
        nuevo_rol = attrs.get('rol', self.instance.rol)
        nuevo_estado = attrs.get('is_active', self.instance.is_active)

        if es_uno_mismo:
            if 'rol' in attrs and attrs['rol'] != self.instance.rol:
                raise serializers.ValidationError({
                    'rol': 'Por seguridad, no puedes cambiar tu propio rol.'
                })
            if 'is_active' in attrs and not attrs['is_active']:
                raise serializers.ValidationError({
                    'is_active': 'Por seguridad, no puedes desactivar tu propia cuenta.'
                })

        # Protección adicional: si el usuario editado es el último administrador
        # activo, no se le puede quitar el rol ni desactivar.
        era_admin_activo = (
            self.instance.rol == 'administrador' and self.instance.is_active
        )
        seguira_siendo_admin_activo = (
            nuevo_rol == 'administrador' and nuevo_estado
        )
        if era_admin_activo and not seguira_siendo_admin_activo:
            otros_admins = User.objects.filter(
                rol='administrador', is_active=True
            ).exclude(pk=self.instance.pk)
            if not otros_admins.exists():
                raise serializers.ValidationError(
                    'Debe existir al menos un administrador activo en el sistema.'
                )

        return attrs

class AdminUsuarioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'rol',
            'is_active',
            'date_joined',
            'last_login',
        )
        read_only_fields = fields