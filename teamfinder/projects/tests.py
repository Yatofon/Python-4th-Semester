from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import Project

User = get_user_model()


class ProjectModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            name='Project',
            surname='Owner',
            phone='+79991112233',
            password='ownerpass123'
        )
        
        self.project_data = {
            'name': 'Test Project',
            'description': 'This is a test project description',
            'owner': self.user,
            'github_url': 'https://github.com/test/project',
            'status': 'open'
        }
    
    def test_create_project(self):
        project = Project.objects.create(**self.project_data)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.owner, self.user)
        self.assertEqual(project.status, 'open')
        self.assertIsNotNone(project.created_at)
    
    def test_project_str_method(self):
        project = Project.objects.create(**self.project_data)
        self.assertEqual(str(project), 'Test Project')
    
    def test_is_owner_method(self):
        project = Project.objects.create(**self.project_data)
        another_user = User.objects.create_user(
            email='other@example.com',
            name='Other',
            surname='User',
            phone='+79995556677',
            password='other123'
        )
        self.assertTrue(project.is_owner(self.user))
        self.assertFalse(project.is_owner(another_user))
    
    def test_is_participant_method(self):
        project = Project.objects.create(**self.project_data)
        project.participants.add(self.user)
        self.assertTrue(project.is_participant(self.user))
    
    def test_default_status(self):
        project = Project.objects.create(
            name='Default Status Project',
            owner=self.user
        )
        self.assertEqual(project.status, 'open')
    
    def test_participants_many_to_many(self):
        project = Project.objects.create(**self.project_data)
        another_user = User.objects.create_user(
            email='participant@example.com',
            name='Participant',
            surname='User',
            phone='+79997778899',
            password='part123'
        )
        project.participants.add(another_user)
        self.assertTrue(project.is_participant(another_user))
        self.assertEqual(project.participants.count(), 1)


class ProjectListViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='test123'
        )
        
        self.project1 = Project.objects.create(
            name='Project 1',
            description='First project',
            owner=self.user,
            created_at='2024-01-01 10:00:00'
        )
        self.project2 = Project.objects.create(
            name='Project 2',
            description='Second project',
            owner=self.user,
            created_at='2024-01-02 10:00:00'
        )
    
    def test_project_list_page(self):
        response = self.client.get('/projects/list/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_list.html')
        self.assertContains(response, 'Project 1')
        self.assertContains(response, 'Project 2')
    
    def test_projects_ordered_by_created_at_desc(self):
        response = self.client.get('/projects/list/')
        projects = response.context['projects']
        self.assertEqual(projects[0].name, 'Project 2')
        self.assertEqual(projects[1].name, 'Project 1')
    
    def test_only_open_projects_shown(self):
        closed_project = Project.objects.create(
            name='Closed Project',
            description='Closed',
            owner=self.user,
            status='closed'
        )
        response = self.client.get('/projects/list/')
        projects = response.context['projects']
        self.assertIn(self.project1, projects)
        self.assertIn(self.project2, projects)
        self.assertNotIn(closed_project, projects)
    
    def test_project_list_pagination(self):
        for i in range(15):
            Project.objects.create(
                name=f'Project {i}',
                owner=self.user
            )
        response = self.client.get('/projects/list/')
        self.assertEqual(len(response.context['projects']), 12)


class ProjectDetailViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='test123'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            owner=self.user,
            github_url='https://github.com/test/project'
        )
        self.project.participants.add(self.user)
    
    def test_project_detail_page(self):
        response = self.client.get(f'/projects/{self.project.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')
        self.assertContains(response, 'Test Description')
    
    def test_project_detail_404_for_nonexistent(self):
        response = self.client.get('/projects/99999/')
        self.assertEqual(response.status_code, 404)
    
    def test_context_has_is_participant_for_auth_user(self):
        self.client.login(email='user@example.com', password='test123')
        response = self.client.get(f'/projects/{self.project.pk}/')
        self.assertTrue(response.context['is_participant'])
    
    def test_context_has_is_favorite_for_auth_user(self):
        self.client.login(email='user@example.com', password='test123')
        self.user.favorites.add(self.project)
        response = self.client.get(f'/projects/{self.project.pk}/')
        self.assertTrue(response.context['is_favorite'])


class ProjectCreateViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='test123'
        )
    
    def test_create_project_page_requires_login(self):
        response = self.client.get('/projects/create-project/')
        self.assertRedirects(response, '/users/login/?next=/projects/create-project/')
    
    def test_create_project_logged_in(self):
        self.client.login(email='user@example.com', password='test123')
        response = self.client.post('/projects/create-project/', {
            'name': 'New Project',
            'description': 'New Description',
            'github_url': 'https://github.com/new/project',
            'status': 'open'
        })
        new_project = Project.objects.latest('id')
        self.assertRedirects(response, f'/projects/{new_project.pk}/')
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(new_project.name, 'New Project')
        self.assertEqual(new_project.owner, self.user)
        self.assertTrue(new_project.is_participant(self.user))
    
    def test_create_project_without_github_url(self):
        self.client.login(email='user@example.com', password='test123')
        response = self.client.post('/projects/create-project/', {
            'name': 'No GitHub Project',
            'description': 'Description',
            'github_url': '',
            'status': 'open'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Project.objects.count(), 1)
    
    def test_create_project_invalid_github_url(self):
        self.client.login(email='user@example.com', password='test123')
        response = self.client.post('/projects/create-project/', {
            'name': 'Invalid URL Project',
            'description': 'Description',
            'github_url': 'not-a-url',
            'status': 'open'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Project.objects.count(), 0)
        self.assertContains(response, 'Введите правильный URL')


class ProjectEditViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='test123'
        )
        
        self.project = Project.objects.create(
            name='Original Name',
            description='Original Description',
            owner=self.user
        )
    
    def test_edit_project_page_requires_login(self):
        response = self.client.get(f'/projects/{self.project.pk}/edit/')
        self.assertRedirects(response, f'/users/login/?next=/projects/{self.project.pk}/edit/')
    
    def test_edit_project_owner_only(self):
        another_user = User.objects.create_user(
            email='other@example.com',
            name='Other',
            surname='User',
            phone='+79998887766',
            password='other123'
        )
        self.client.login(email='other@example.com', password='other123')
        response = self.client.get(f'/projects/{self.project.pk}/edit/')
        self.assertRedirects(response, f'/projects/{self.project.pk}/')
    
    def test_edit_project_success(self):
        self.client.login(email='user@example.com', password='test123')
        response = self.client.post(f'/projects/{self.project.pk}/edit/', {
            'name': 'Updated Name',
            'description': 'Updated Description',
            'github_url': 'https://github.com/updated/project',
            'status': 'closed'
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Name')
        self.assertEqual(self.project.status, 'closed')
    
    def test_edit_project_admin_can_edit(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            name='Admin',
            surname='User',
            phone='+79990001122',
            password='admin123'
        )
        self.client.login(email='admin@example.com', password='admin123')
        response = self.client.post(f'/projects/{self.project.pk}/edit/', {
            'name': 'Admin Updated',
            'description': 'Updated by admin',
            'github_url': '',
            'status': 'open'
        })
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Admin Updated')


class ProjectActionsTest(TestCase):
    
    def setUp(self):
        self.owner = User.objects.create_user(
            email='owner@example.com',
            name='Owner',
            surname='User',
            phone='+79991112233',
            password='owner123'
        )
        
        self.participant = User.objects.create_user(
            email='participant@example.com',
            name='Participant',
            surname='User',
            phone='+79992223344',
            password='part123'
        )
        
        self.project = Project.objects.create(
            name='Test Project',
            owner=self.owner,
            status='open'
        )
    
    def test_toggle_participate_add(self):
        self.client.login(email='participant@example.com', password='part123')
        response = self.client.post(f'/projects/{self.project.pk}/toggle-participate/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.project.is_participant(self.participant))
        self.assertEqual(response.json()['is_participant'], True)
    
    def test_toggle_participate_remove(self):
        self.project.participants.add(self.participant)
        self.client.login(email='participant@example.com', password='part123')
        response = self.client.post(f'/projects/{self.project.pk}/toggle-participate/')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.project.is_participant(self.participant))
        self.assertEqual(response.json()['is_participant'], False)
    
    def test_toggle_participate_requires_login(self):
        response = self.client.post(f'/projects/{self.project.pk}/toggle-participate/')
        self.assertEqual(response.status_code, 302)
    
    def test_complete_project_owner(self):
        self.client.login(email='owner@example.com', password='owner123')
        response = self.client.post(f'/projects/{self.project.pk}/complete/')
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'closed')
        self.assertEqual(response.json()['project_status'], 'closed')
    
    def test_complete_project_non_owner(self):
        self.client.login(email='participant@example.com', password='part123')
        response = self.client.post(f'/projects/{self.project.pk}/complete/')
        self.assertEqual(response.status_code, 403)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, 'open')
    
    def test_complete_already_closed_project(self):
        self.project.status = 'closed'
        self.project.save()
        self.client.login(email='owner@example.com', password='owner123')
        response = self.client.post(f'/projects/{self.project.pk}/complete/')
        self.assertEqual(response.json()['status'], 'error')
    
    def test_toggle_favorite(self):
        self.client.login(email='participant@example.com', password='part123')
        response = self.client.post(f'/projects/{self.project.pk}/toggle-favorite/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.participant.favorites.filter(pk=self.project.pk).exists())
        self.assertTrue(response.json()['favorited'])
        
        response = self.client.post(f'/projects/{self.project.pk}/toggle-favorite/')
        self.assertFalse(self.participant.favorites.filter(pk=self.project.pk).exists())
        self.assertFalse(response.json()['favorited'])


class FavoriteProjectsViewTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='test123'
        )
        
        self.project1 = Project.objects.create(
            name='Favorite 1',
            owner=self.user
        )
        self.project2 = Project.objects.create(
            name='Favorite 2',
            owner=self.user
        )
    
    def test_favorites_page_requires_login(self):
        response = self.client.get('/projects/favorites/')
        self.assertRedirects(response, '/users/login/?next=/projects/favorites/')
    
    def test_favorites_page_shows_favorite_projects(self):
        self.user.favorites.add(self.project1, self.project2)
        self.client.login(email='user@example.com', password='test123')
        response = self.client.get('/projects/favorites/')
        self.assertContains(response, 'Favorite 1')
        self.assertContains(response, 'Favorite 2')
    
    def test_favorites_page_empty(self):
        self.client.login(email='user@example.com', password='test123')
        response = self.client.get('/projects/favorites/')
        self.assertContains(response, 'У вас пока нет избранных проектов')


class ProjectFilterTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            name='Test',
            surname='User',
            phone='+79991234567',
            password='test123'
        )
    
    def test_homepage_redirects_to_project_list(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/projects/list/')