from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, User


class StaticFormTests(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.user = User.objects.create_user(username='NameUser')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="NoNameUser")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            pk=1
        )
        self.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.post.author)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.id,
                author=self.user
            ).exists()
        )
        self.assertEqual(response.status_code, 200)

    def test_post_edit(self):
        posts_count = Post.objects.count()
        form_data = {'text': "Изменения в тексте", "group": self.group.id}
        response = self.authorized_client.post(
            reverse('posts:edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())
        self.assertEqual(response.status_code, 200)

    def test_post_create_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {'text': self.post.text, 'group': self.group.id}
        response = self.guest_client.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, "/auth/login/?next=/create/")
        self.assertEqual(Post.objects.count(), posts_count == 1)
        self.assertEqual(response.status_code, 200)

    def test_post_edit_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {"text": "Изменения в тексте", "group": self.group.id}
        response = self.guest_client.post(
            reverse("posts:edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text=form_data['text']).exists())
        self.assertEqual(response.status_code, 200)

    def test_post_edit_another_author_client(self):
        posts_count = Post.objects.count()
        form_data = {"text": "Изменения в тексте", "group": self.group.id}
        response = self.another_authorized_client.post(
            reverse("posts:edit", args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(text=self.post.text).exists())
        self.assertEqual(response.status_code, 200)
