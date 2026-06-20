from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Categoria, Estado


class AuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Estado.objects.get_or_create(nombre_estado='Pendiente')
        Categoria.objects.get_or_create(nombre='Alumbrado')

    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_returns_token(self):
        response = self.client.post('/auth/register/', {
            'name': 'Maria', 'lastname': 'Gomez', 'username': '87654321',
            'phone': '1122223333', 'password': 'securepass',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['name'], 'Maria')
        self.assertEqual(response.data['user']['lastname'], 'Gomez')
        self.assertEqual(response.data['user']['dni'], '87654321')
        self.assertEqual(response.data['user']['phone'], '1122223333')
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)

    def test_register_duplicate_dni_fails(self):
        self.client.post('/auth/register/', {
            'name': 'A', 'lastname': 'B', 'username': '11111111',
            'password': 'pass1234',
        }, format='json')

        response = self.client.post('/auth/register/', {
            'name': 'C', 'lastname': 'D', 'username': '11111111',
            'password': 'pass1234',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        self.client.post('/auth/register/', {
            'name': 'Pedro', 'lastname': 'Lopez', 'username': '99999999',
            'password': 'mypassword',
        }, format='json')
        response = self.client.post('/auth/login/', {
            'username': '99999999', 'password': 'mypassword',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['name'], 'Pedro')

    def test_login_wrong_password(self):
        self.client.post('/auth/register/', {
            'name': 'Pedro', 'lastname': 'Lopez', 'username': '99999999',
            'password': 'mypassword',
        }, format='json')
        response = self.client.post('/auth/login/', {
            'username': '99999999', 'password': 'wrongpass',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        response = self.client.post('/auth/login/', {
            'username': '00000000', 'password': 'whatever',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update(self):
        reg = self.client.post('/auth/register/', {
            'name': 'Ana', 'lastname': 'Diaz', 'username': '55555555',
            'password': 'pass1234',
        }, format='json')
        user_id = reg.data['user']['id']
        token = reg.data['token']

        response = self.client.put(
            f'/auth/upload/{user_id}/',
            {'name': 'Anabella', 'lastname': 'Diaz', 'phone': '44445555'},
            format='json', HTTP_AUTHORIZATION=f'Token {token}',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Anabella')
        self.assertEqual(response.data['phone'], '44445555')

    def test_profile_update_other_user_forbidden(self):
        self.client.post('/auth/register/', {
            'name': 'A', 'lastname': 'B', 'username': '11111111',
            'password': 'pass1234',
        }, format='json')
        reg2 = self.client.post('/auth/register/', {
            'name': 'C', 'lastname': 'D', 'username': '22222222',
            'password': 'pass1234',
        }, format='json')
        token2 = reg2.data['token']

        response = self.client.put(
            '/auth/upload/1/', {'name': 'Hacker'},
            format='json', HTTP_AUTHORIZATION=f'Token {token2}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class DenunciaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Estado.objects.get_or_create(nombre_estado='Pendiente')
        cls.cat_alumbrado = Categoria.objects.get_or_create(nombre='Alumbrado')[0]
        cls.cat_bache = Categoria.objects.get_or_create(nombre='Bache')[0]

    def setUp(self):
        self.client = APIClient()
        reg = self.client.post('/auth/register/', {
            'name': 'Test', 'lastname': 'User', 'username': '11111111',
            'password': 'pass1234',
        }, format='json')
        self.token = reg.data['token']
        self.user_id = reg.data['user']['id']

        reg2 = self.client.post('/auth/register/', {
            'name': 'Other', 'lastname': 'Guy', 'username': '22222222',
            'password': 'pass1234',
        }, format='json')
        self.other_token = reg2.data['token']

    def test_create_denuncia(self):
        response = self.client.post('/api/denuncias/', {
            'id_categoria': self.cat_alumbrado.id_categoria,
            'descripcion': 'Bache en la calle',
            'latitud': -24.782932,
            'longitud': -65.412155,
            'direccion': 'Calle Falsa 123',
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['descripcion'], 'Bache en la calle')
        self.assertEqual(response.data['latitud'], '-24.782932')
        self.assertEqual(response.data['estado_actual']['nombre_estado'], 'Pendiente')

    def test_list_my_denuncias(self):
        self.client.post('/api/denuncias/', {
            'id_categoria': self.cat_alumbrado.id_categoria,
            'descripcion': 'Denuncia 1',
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        self.client.post('/api/denuncias/', {
            'id_categoria': self.cat_bache.id_categoria,
            'descripcion': 'Denuncia 2',
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.other_token}')

        response = self.client.get(
            '/api/denuncias/', HTTP_AUTHORIZATION=f'Token {self.token}'
        )
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['descripcion'], 'Denuncia 1')

    def test_update_own_denuncia(self):
        create_resp = self.client.post('/api/denuncias/', {
            'id_categoria': self.cat_alumbrado.id_categoria,
            'descripcion': 'Original',
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        denuncia_id = create_resp.data['id_denuncia']
        response = self.client.put(
            f'/api/denuncias/{denuncia_id}/',
            {'id_categoria': self.cat_bache.id_categoria,
             'descripcion': 'Modificada'},
            format='json', HTTP_AUTHORIZATION=f'Token {self.token}',
        )
        self.assertEqual(response.data['descripcion'], 'Modificada')

    def test_cannot_update_others_denuncia(self):
        create_resp = self.client.post('/api/denuncias/', {
            'id_categoria': self.cat_alumbrado.id_categoria,
            'descripcion': 'Mia',
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        denuncia_id = create_resp.data['id_denuncia']
        response = self.client.put(
            f'/api/denuncias/{denuncia_id}/',
            {'descripcion': 'Hackeada'},
            format='json', HTTP_AUTHORIZATION=f'Token {self.other_token}',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_denied(self):
        response = self.client.post('/api/denuncias/', {
            'id_categoria': self.cat_alumbrado.id_categoria,
            'descripcion': 'Anonima',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VotoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Estado.objects.get_or_create(nombre_estado='Pendiente')
        cls.cat = Categoria.objects.get_or_create(nombre='Alumbrado')[0]

    def setUp(self):
        self.client = APIClient()

        reg = self.client.post('/auth/register/', {
            'name': 'A', 'lastname': 'B', 'username': '11111111',
            'password': 'pass1234',
        }, format='json')
        self.token = reg.data['token']

        reg2 = self.client.post('/auth/register/', {
            'name': 'C', 'lastname': 'D', 'username': '22222222',
            'password': 'pass1234',
        }, format='json')
        self.other_token = reg2.data['token']

        create = self.client.post('/api/denuncias/', {
            'id_categoria': self.cat.id_categoria,
            'descripcion': 'Para votar',
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')
        self.denuncia_id = create.data['id_denuncia']

    def test_vote_on_denuncia(self):
        response = self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_duplicate_vote_returns_409(self):
        self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        response = self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_list_votes_by_denuncia(self):
        self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')
        self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.other_token}')

        response = self.client.get(
            f'/api/votos/?denuncia={self.denuncia_id}',
            HTTP_AUTHORIZATION=f'Token {self.token}',
        )
        self.assertEqual(response.data['count'], 2)

    def test_delete_own_vote(self):
        vote = self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        vote_id = vote.data['id_voto']
        response = self.client.delete(
            f'/api/votos/{vote_id}/',
            HTTP_AUTHORIZATION=f'Token {self.token}',
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_delete_others_vote(self):
        vote = self.client.post('/api/votos/', {
            'id_denuncia': self.denuncia_id,
        }, format='json', HTTP_AUTHORIZATION=f'Token {self.token}')

        vote_id = vote.data['id_voto']
        response = self.client.delete(
            f'/api/votos/{vote_id}/',
            HTTP_AUTHORIZATION=f'Token {self.other_token}',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
