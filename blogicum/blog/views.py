from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (
    CreateView, DeleteView, UpdateView, DetailView, ListView
)

from blogicum.settings import POSTS_LIMIT

from blog.models import Post, Category, Comment
from blog.forms import PostForm, CommentForm


@login_required
def add_comment(request, comment_id):
    post = get_object_or_404(Post, pk=comment_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    else:
        return render(request, 'blog/comment.html',
                      {'form': form, 'post': post})
    return redirect('blog:post_detail', post_id=comment_id)


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class CommentMixin(OnlyAuthorMixin):
    template_name = 'blog/comment.html'
    model = Comment

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.kwargs['post_id']}
        )


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_LIMIT

    def filter_posts(self):
        return Post.objects.select_related(
            'author', 'location', 'category').filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )

    def get_queryset(self):
        return self.filter_posts().annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = POSTS_LIMIT

    def get_category(self):
        return get_object_or_404(
            Category.objects.filter(is_published=True),
            slug=self.kwargs['category_slug']
        )

    def get_queryset(self):
        selected_category = self.get_category()
        related_posts = Post.objects.filter(
            category=selected_category,
            pub_date__lte=timezone.now(),
            is_published=True,
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')
        if not selected_category.is_published:
            raise Http404("Category not found")
        return related_posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.get_category()
        context['category'] = category
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        # Присвоить полю author объект пользователя из запроса.
        form.instance.author = self.request.user
        # Продолжить валидацию, описанную в форме.
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    post_key = 'post_id'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if isinstance(self.object, Post):
            context['form'] = CommentForm()
            context['comments'] = (
                self.object.comments.select_related('author'))
        return context

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        if not post.is_published and post.author != self.request.user:
            raise Http404("Нет доступа к этой странице")
        return post


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    template_name = 'blog/create.html'
    model = Post
    form_class = PostForm
    pk_url_kwarg = 'post_id'

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])

    def get_success_url(self):
        return reverse_lazy('blog:post_detail', kwargs={
            'post_id': self.object.id})


class PostDeleteView(OnlyAuthorMixin, LoginRequiredMixin, DeleteView):
    template_name = 'blog/create.html'
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm

    def get_success_url(self):
        return reverse_lazy('blog:profile', kwargs={
            'username': self.request.user.username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        context['form'] = PostForm(instance=post)
        return context


class UserProfileView(ListView):
    model = Post
    template_name = 'blog/profile.html'
    paginate_by = POSTS_LIMIT

    def get_user(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        selected_user = self.get_user()
        related_posts = Post.objects.filter(author=selected_user).annotate(
            comment_count=Count('comments')).order_by('-pub_date')
        if selected_user != self.request.user:
            related_posts = Post.objects.filter(
                author=selected_user,
                pub_date__lte=timezone.now(),
                is_published=True,
            ).annotate(
                comment_count=Count('comments')).order_by('-pub_date')
        return related_posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_user()
        return context


class UserEditView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/user.html'
    model = User
    fields = ['first_name', 'last_name', 'email']

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile', kwargs={'username': self.object.username}
        )


class CommentUpdateView(CommentMixin, UpdateView):
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != self.request.user:
            return redirect('blog:post_detail', post_id=self.kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)


class CommentDeleteView(CommentMixin, DeleteView):
    pass
