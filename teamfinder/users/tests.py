from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image
import io
import tempfile

User = get_user_model()

def get_image_file():
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return SimpleUploadedFile(file.name, file.read(), content_type='image/png')

class UserModelTest(TestCase):
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'name': 'Test',
            'surname': 'User',
            'phone': '+79991234567',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.get_full_name(), 'Test User')
    
    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin',
            surname='User',
            phone='+79991112233',
            password='adminpass123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_user_str_method(self):
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'Test User')
    
    def test_phone_normalization_from_8(self):
        user = User.objects.create_user(
            email='phone@example.com',
            name='Phone',
            surname='Test',
            phone='89991234567',
            password='test123'
        )
        self.assertEqual(user.phone, '+79991234567')
    
    def test_phone_normalization_without_plus(self):
        user = User.objects.create_user(
            email='phone2@example.com',
            name='Phone2',
            surname='Test',
            phone='79991234567',
            password='test123'
        )
        self.assertEqual(user.phone, '+79991234567')
    
    def test_unique_phone(self):
        User.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test2@example.com',
                name='Test2',
                surname='User2',
                phone='+79991234567',
                password='test123'
            )
    
    def test_unique_email(self):
        User.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                name='Test2',
                surname='User2',
                phone='+79998887777',
                password='test123'
            )
    
    def test_avatar_generation_on_create(self):
        user = User.objects.create_user(**self.user_data)
        self.assertIsNotNone(user.avatar)
        self.assertTrue(user.avatar.name.startswith('avatars/avatar_'))
    
    def test_favorites_relation(self):
        from projects.models import Project
        user = User.objects.create_user(**self.user_data)
        project = Project.objects.create(
            name='Test Project',
            owner=user
        )
        user.favorites.add(project)
        self.assertTrue(user.favorites.filter(id=project.id).exists())


class UserRegistrationTest(TestCase):
    
    def test_registration_page_status(self):
        response = self.client.get('/users/register/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
    
    def test_successful_registration(self):
        response = self.client.post('/users/register/', {
            'name': 'New',
            'surname': 'User',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        })
        self.assertRedirects(response, '/projects/list/')
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
    
    def test_registration_password_mismatch(self):
        response = self.client.post('/users/register/', {
            'name': 'New',
            'surname': 'User',
            'email': 'newuser@example.com',
            'password': 'testpass123',
            'password_confirm': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_registration_duplicate_email(self):
        User.objects.create_user(
            email='existing@example.com',
            name='Existing',
            surname='User',
            phone='+79991234567',
            password='pass123'
        )
        response = self.client.post('/users/register/', {
            'name': 'New',
            'surname': 'User',
            'email': 'existing@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Пользователь с таким email уже существует')


class UserLoginTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='testpass123'
        )
    
    def test_login_page_status(self):
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
    
    def test_successful_login(self):
        response = self.client.post('/users/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertRedirects(response, '/projects/list/')
    
    def test_failed_login_wrong_password(self):
        response = self.client.post('/users/login/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный имейл или пароль')
    
    def test_failed_login_wrong_email(self):
        response = self.client.post('/users/login/', {
            'email': 'wrong@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Неверный имейл или пароль')


class UserProfileTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='testpass123'
        )
    
    def test_profile_page_accessible(self):
        response = self.client.get(f'/users/{self.user.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test User')
    
    def test_profile_page_404_for_nonexistent(self):
        response = self.client.get('/users/99999/')
        self.assertEqual(response.status_code, 404)
    
    def test_edit_profile_page_requires_login(self):
        response = self.client.get('/users/edit/')
        self.assertRedirects(response, '/users/login/?next=/users/edit/')
    
    def test_edit_profile_logged_in(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.post('/users/edit/', {
            'name': 'Updated',
            'surname': 'Name',
            'phone': '+79998887766',
            'about': 'New about text',
            'github_url': 'https://github.com/testuser'
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated')
        self.assertEqual(self.user.surname, 'Name')
        self.assertEqual(self.user.about, 'New about text')
    
    def test_logout(self):
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get('/users/logout/')
        self.assertRedirects(response, '/projects/list/')
        self.assertNotIn('_auth_user_id', self.client.session)


class UserListViewTest(TestCase):
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            name='User',
            surname='One',
            phone='+79991111111',
            password='pass123'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            name='User',
            surname='Two',
            phone='+79992222222',
            password='pass123'
        )
    
    def test_users_list_page(self):
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User One')
        self.assertContains(response, 'User Two')
    
    def test_users_list_pagination(self):
        for i in range(15):
            User.objects.create_user(
                email=f'user{i}@example.com',
                name=f'User{i}',
                surname=f'Surname{i}',
                phone=f'+799900000{i:02d}',
                password='pass123'
            )
        response = self.client.get('/users/list/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['participants']), 12)
    
    def test_filter_favorite_authors_requires_login(self):
        response = self.client.get('/users/list/?filter=favorite_authors')
        self.assertEqual(response.status_code, 200)
        # Неавторизованный пользователь не видит фильтрацию
        self.assertIsNone(response.context.get('active_filter'))