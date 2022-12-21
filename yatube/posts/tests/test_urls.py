from django.test import TestCase, Client

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста'
        )
        cls.HOME_PG = '/'
        cls.GROUP_PG = f'/group/{StaticURLTests.group.slug}/'
        cls.PROFILE_PG = f'/profile/{StaticURLTests.user.username}/'
        cls.DETAIL_PG = f'/posts/{StaticURLTests.post.id}/'
        cls.CREATE_PG = '/create/'
        cls.EDIT_PG = f'/posts/{StaticURLTests.post.id}/edit/'

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoNameUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(StaticURLTests.post.author)

    # Доступность страниц для всех
    def test_home_url_exists_at_desired_location(self):
        response = self.guest_client.get(self.HOME_PG)
        self.assertEqual(response.status_code, 200)

    def test_group_url_exists_at_desired_location(self):
        response = self.guest_client.get(self.GROUP_PG)
        self.assertEqual(response.status_code, 200)

    def test_user_profile_url_exists_at_desired_location(self):
        response = self.guest_client.get(self.PROFILE_PG)
        self.assertEqual(response.status_code, 200)

    def test_post_id_url_exists_at_desired_location(self):
        response = self.guest_client.get(self.DETAIL_PG)
        self.assertEqual(response.status_code, 200)

    def test_unexist_url_exists_at_desired_location(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    # Доступность страницы для автора
    def test_post_edit_url_exists_at_desired_location(self):
        response = self.another_authorized_client.get(self.EDIT_PG)
        self.assertEqual(response.status_code, 200)

    # Доступность страницы для авторизованного
    def test_create_url_exists_at_desired_location_authorized(self):
        response = self.authorized_client.get(self.CREATE_PG)
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            self.HOME_PG: 'posts/index.html',
            self.GROUP_PG: 'posts/group_list.html',
            self.PROFILE_PG: 'posts/profile.html',
            self.DETAIL_PG: 'posts/post_detail.html',
            self.CREATE_PG: 'posts/create_post.html',
            self.EDIT_PG: 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.another_authorized_client.get(address)
                self.assertTemplateUsed(response, template)
