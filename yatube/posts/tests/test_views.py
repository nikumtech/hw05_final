from django.test import Client, TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User, Comment, Follow

POSTS_PER_PAGE = 10


class StaticPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="picture.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group,
            image=cls.uploaded
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoNameUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(
            StaticPagesTests.post.author
        )

    # Проверяем шаблоны
    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': StaticPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': StaticPagesTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': StaticPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:edit',
                kwargs={'post_id': StaticPagesTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.another_authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверяем контексты
    def test_index_show_correct_context(self):
        response = self.guest_client.get(reverse("posts:index"))
        expected = list(Post.objects.all()[:POSTS_PER_PAGE])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_show_correct_context(self):
        response = self.guest_client.get(
            reverse("posts:group_list",
                    kwargs={"slug": StaticPagesTests.group.slug}
                    )
        )
        expected = list(Post.objects.filter(
            group_id=StaticPagesTests.group.id
        )[:POSTS_PER_PAGE])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_profile_show_correct_context(self):
        response = self.guest_client.get(
            reverse("posts:profile", args=(StaticPagesTests.post.author,))
        )
        expected = list(Post.objects.filter(
            author_id=StaticPagesTests.user
        )[:POSTS_PER_PAGE])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_post_detail_show_correct_context(self):
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(
            response.context.get("post").text, StaticPagesTests.post.text
        )
        self.assertEqual(
            response.context.get("post").author, StaticPagesTests.post.author
        )
        self.assertEqual(
            response.context.get("post").group, StaticPagesTests.post.group
        )

    def test_create_show_correct_context(self):
        response = self.another_authorized_client.get(reverse("posts:create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_show_correct_context(self):
        response = self.another_authorized_client.get(
            reverse("posts:edit", kwargs={"post_id": StaticPagesTests.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_not_in_mistake_group_list_page(self):
        form_fields = {
            reverse(
                "posts:group_list",
                kwargs={"slug": StaticPagesTests.group.slug}
            ): Post.objects.exclude(group=StaticPagesTests.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.another_authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_check_group_in_pages(self):
        form_fields = {
            reverse("posts:index"):
            Post.objects.get(group=StaticPagesTests.post.group),
            reverse(
                "posts:profile",
                kwargs={"username": StaticPagesTests.post.author}
            ): Post.objects.get(group=StaticPagesTests.post.group),
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    # Тесты для картинок
    def test_image_in_index_and_profile_page(self):
        templates = (
            reverse("posts:index"),
            reverse("posts:group_list", kwargs={"slug": self.group.slug}),
            reverse("posts:profile", kwargs={"username": self.post.author})
        )
        for url in templates:
            with self.subTest(url):
                response = self.guest_client.get(url)
                obj = response.context["page_obj"][0]
                self.assertEqual(obj.image, self.post.image)

    def test_image_in_post_detail_page(self):
        response = self.guest_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        obj = response.context["post"]
        self.assertEqual(obj.image, self.post.image)

    def test_image_in_page(self):
        self.assertTrue(
            Post.objects.filter(image="posts/picture.gif").exists()
        )

    # Тест комментариев
    def test_comment_correct_context(self):
        comments_count = Comment.objects.count()
        form_data = {'text': "Тестовый комментарий"}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(Comment.objects.filter(
            text=form_data['text']
        ).exists())

    # Проверка кэша
    def test_check_cache(self):
        response = self.guest_client.get(reverse('posts:index'))
        check1 = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(reverse('posts:index'))
        check2 = response2.content
        self.assertEqual(check1, check2)

    # Проверка подписок/отписок
    def test_follow(self):
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)
        Follow.objects.get_or_create(user=self.user, author=self.post.author)
        check1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(check1.context['page_obj']), 1)
        self.assertIn(self.post, check1.context['page_obj'])
        another = User.objects.create(username='UserNew')
        self.authorized_client.force_login(another)
        check1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, check1.context['page_obj'])
        Follow.objects.all().delete()
        check2 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(check2.context['page_obj']), 0)
