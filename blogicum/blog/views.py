from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings as s
from django.db.models import Count
from django.http import Http404
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import (
    CreateView, DeleteView, UpdateView, DetailView, ListView
)

from blog.models import Post, Category
from blog.forms import PostForm, CommentForm
from blog.mixins import OnlyAuthorMixin, CommentMixin


def filter_posts(
        manager=Post.objects, apply_filters=True, add_annotations=False
):

    queryset = manager.select_related('author', 'location', 'category')

    if apply_filters:
        queryset = queryset.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )

    if add_annotations:
        queryset = queryset.annotate(
            comment_count=Count('comments')
        ).order_by('-comment_count')

    return queryset


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


class IndexView(ListView):
    model = Post
    template_name = 'blog/index.html'
    paginate_by = s.POSTS_LIMIT

    def get_queryset(self):
        return filter_posts(
            manager=Post.objects,
            apply_filters=True,
            add_annotations=True
        ).order_by('-pub_date')


class CategoryPostsView(ListView):
    model = Post
    template_name = 'blog/category.html'
    paginate_by = s.POSTS_LIMIT

    def get_category(self):
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_queryset(self):
        selected_category = self.get_category()
        return filter_posts(
            manager=selected_category.posts,
            apply_filters=True,
            add_annotations=True
        ).order_by('-pub_date')

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
        form.instance.author = self.request.user
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
    paginate_by = s.POSTS_LIMIT

    def get_user(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        selected_user = self.get_user()
        queryset = filter_posts(
            apply_filters=selected_user != self.request.user,
            add_annotations=True
        ).filter(author=selected_user).order_by('-pub_date')
        return queryset


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


class CommentUpdateView(CommentMixin, OnlyAuthorMixin, UpdateView):
    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    pass
