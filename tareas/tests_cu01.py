from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


def password_de(longitud):
    patron = 'Ab1!' * ((longitud // 4) + 1)
    return patron[:longitud]


PASSWORD = password_de(12)


class RegistroCU01Base(APITestCase):
    def registrar(self, nombre='José Pérez', email=None, password=PASSWORD):
        return self.client.post(
            '/api/register/',
            {'username': nombre, 'email': email, 'password': password},
            format='json',
        )

    def crear_cuenta_previa(self, email='jose@gmail.com'):
        return User.objects.create_user(
            username='cuenta_previa_cu01',
            email=email,
            password=PASSWORD,
            rol='usuario',
        )


class CU01ParticionesEquivalenciaTests(RegistroCU01Base):
    def test_cp01_nombre_vacio(self):
        response = self.registrar(nombre='', email='jose.cp01@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_cp02_registro_valido_jose_perez(self):
        response = self.registrar(email='jose.cp02@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        usuario = User.objects.get(email='jose.cp02@gmail.com')
        self.assertEqual(usuario.nombre_completo, 'José Pérez')
        self.assertEqual(usuario.rol, 'usuario')

    def test_cp03_correo_vacio(self):
        response = self.registrar(email='')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_cp04_correo_valido(self):
        response = self.registrar(email='jose.cp04@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='jose.cp04@gmail.com').exists())

    def test_cp05_correo_sin_extension(self):
        response = self.registrar(email='jose@gmail')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_cp06_correo_sin_arroba(self):
        response = self.registrar(email='jose')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_cp07_correo_sin_arroba_con_puntos(self):
        response = self.registrar(email='jose.gmail.com')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_cp08_contrasena_vacia(self):
        response = self.registrar(
            email='jose.cp08@gmail.com', password=''
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_cp09_contrasena_cinco_caracteres(self):
        response = self.registrar(
            email='jose.cp09@gmail.com', password=password_de(5)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_cp10_contrasena_ocho_caracteres(self):
        response = self.registrar(
            email='jose.cp10@gmail.com', password=password_de(8)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cp11_contrasena_veintitres_caracteres(self):
        response = self.registrar(
            email='jose.cp11@gmail.com', password=password_de(23)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_cp12_correo_previamente_registrado(self):
        self.crear_cuenta_previa()
        response = self.registrar(email='jose@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class CU01ValoresLimiteTests(RegistroCU01Base):
    def test_cp13_contrasena_siete_se_rechaza(self):
        response = self.registrar(
            email='jose.cp13@gmail.com', password=password_de(7)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_cp14_contrasena_ocho_se_acepta(self):
        response = self.registrar(
            email='jose.cp14@gmail.com', password=password_de(8)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cp15_contrasena_nueve_se_acepta(self):
        response = self.registrar(
            email='jose.cp15@gmail.com', password=password_de(9)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cp16_contrasena_diecinueve_se_acepta(self):
        response = self.registrar(
            email='jose.cp16@gmail.com', password=password_de(19)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cp17_contrasena_veinte_se_acepta(self):
        response = self.registrar(
            email='jose.cp17@gmail.com', password=password_de(20)
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cp18_contrasena_veintiuno_se_rechaza(self):
        response = self.registrar(
            email='jose.cp18@gmail.com', password=password_de(21)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class CU01CausaEfectoTests(RegistroCU01Base):
    def test_cp19_todo_valido_y_disponible(self):
        response = self.registrar(email='jose.cp19@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['mensaje'], 'Registro exitoso.')

    def test_cp20_nombre_vacio(self):
        response = self.registrar(
            nombre='', email='jose.cp20@gmail.com'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertNotIn('email', response.data)
        self.assertNotIn('password', response.data)

    def test_cp21_correo_invalido(self):
        response = self.registrar(email='jose@gmail')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_cp22_contrasena_cinco(self):
        response = self.registrar(
            email='jose.cp22@gmail.com', password=password_de(5)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_cp23_nombre_vacio_y_contrasena_cinco(self):
        response = self.registrar(
            nombre='', email='jose.cp23@gmail.com', password=password_de(5)
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('password', response.data)
        self.assertNotIn('email', response.data)

    def test_cp24_correo_no_disponible(self):
        self.crear_cuenta_previa()
        response = self.registrar(email='jose@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_cp25_nombre_vacio_y_correo_invalido(self):
        response = self.registrar(nombre='', email='jose@gmail')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertNotIn('password', response.data)

    def test_cp26_los_tres_campos_invalidos(self):
        response = self.registrar(nombre='', email='mal', password='123')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)

    def test_cp27_correo_invalido_y_contrasena_cinco(self):
        response = self.registrar(email='jose@gmail', password=password_de(5))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
        self.assertNotIn('username', response.data)


class CU01CompatibilidadTests(RegistroCU01Base):
    def test_dos_usuarios_pueden_compartir_nombre_completo(self):
        primera = self.registrar(email='jose.mismo1@gmail.com')
        segunda = self.registrar(email='jose.mismo2@gmail.com')

        self.assertEqual(primera.status_code, status.HTTP_201_CREATED)
        self.assertEqual(segunda.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            User.objects.filter(nombre_completo='José Pérez').count(), 2
        )

    def test_identificadores_internos_continuan_siendo_unicos(self):
        primera = self.registrar(email='jose.unico1@gmail.com')
        segunda = self.registrar(email='jose.unico2@gmail.com')

        usuario1 = User.objects.get(pk=primera.data['usuario']['id'])
        usuario2 = User.objects.get(pk=segunda.data['usuario']['id'])
        self.assertNotEqual(usuario1.username, usuario2.username)
        self.assertEqual(User.objects.filter(username=usuario1.username).count(), 1)
        self.assertEqual(User.objects.filter(username=usuario2.username).count(), 1)

    def test_campos_de_nombre_no_son_unicos_y_username_si(self):
        self.assertFalse(User._meta.get_field('nombre_completo').unique)
        self.assertTrue(User._meta.get_field('username').unique)

    def test_correo_duplicado_ignora_mayusculas(self):
        self.assertEqual(
            self.registrar(email='jose.duplicado@gmail.com').status_code,
            status.HTTP_201_CREATED,
        )
        respuesta = self.registrar(email='JOSE.DUPLICADO@GMAIL.COM')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', respuesta.data)

    def test_login_y_jwt_siguen_funcionando(self):
        registro = self.registrar(email='jose.jwt@gmail.com')
        username = registro.data['usuario']['username']

        login = self.client.post(
            '/api/login/',
            {'username': username, 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn('access', login.data)
        self.assertIn('refresh', login.data)

        token = self.client.post(
            '/api/token/',
            {'username': username, 'password': PASSWORD},
            format='json',
        )
        self.assertEqual(token.status_code, status.HTTP_200_OK)
        self.assertIn('access', token.data)

    def test_limites_de_contrasena_7_8_20_21(self):
        self.assertEqual(
            self.registrar(
                email='jose.lim7@gmail.com', password=password_de(7)
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            self.registrar(
                email='jose.lim8@gmail.com', password=password_de(8)
            ).status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self.registrar(
                email='jose.lim20@gmail.com', password=password_de(20)
            ).status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            self.registrar(
                email='jose.lim21@gmail.com', password=password_de(21)
            ).status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_errores_multiples_se_devuelven_juntos_y_no_crean_usuario(self):
        total_inicial = User.objects.count()
        response = self.registrar(nombre='', email='mal', password='123')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('password', response.data)
        self.assertEqual(User.objects.count(), total_inicial)

    def test_contrasena_nunca_aparece_en_la_respuesta(self):
        response = self.registrar(email='jose.oculto@gmail.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data['usuario'])
