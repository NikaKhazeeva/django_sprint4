from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.timezone import now
from django.views.generic import CreateView
from django.contrib.auth import logout

from .forms import CommentForm, CustomUserChangeForm, PostForm
from .models import Category, Comment, Post


User = get_user_model()


class CreatePostView(LoginRequiredMixin, CreateView):
    """Создание поста."""

    model = Post
    fields = ['title', 'text', 'category', 'image', 'location', 'pub_date']
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:profile', kwargs={
            'username': self.request.user.username})


class SignUpView(CreateView):
    """Регистрация нового пользователя."""

    form_class = UserCreationForm
    template_name = 'registration/registration_form.html'
    success_url = reverse_lazy('login')


def user_logout(request):
    logout(request)
    return render(request, 'registration/logged_out.html')


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    if request.user == profile:
        posts = Post.objects.filter(author=profile).order_by('-pub_date')
    else:
        posts = Post.objects.filter(
            author=profile,
            is_published=True,
            pub_date__lte=now()
        ).order_by('-pub_date')
    is_owner = request.user.is_authenticated and request.user == profile

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/profile.html', {
        'profile': profile,
        'page_obj': page_obj,
        'is_owner': is_owner,
    })


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/create.html', {'form': form})


def get_published_posts():
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=now(),
        category__is_published=True
    )


def index(request):
    posts = get_published_posts().order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "blog/index.html", {
        "page_obj": page_obj
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    access_denied = (
        not post.is_published
        or not post.category.is_published
        or post.pub_date > now()
    )

    if access_denied and request.user != post.author:
        raise Http404("Пост не найден.")

    comments = post.comments.all()
    form = CommentForm()

    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    posts = get_published_posts().filter(category=category)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "blog/category.html", {
        "category": category,
        "page_obj": page_obj
    })


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/post_detail.html',
                  {'post': post, 'form': form})


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        return HttpResponseForbidden("Нельзя редактировать чужой комментарий.")

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    if request.user != comment.author:
        return HttpResponseForbidden("Нельзя удалить чужой комментарий.")

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html',
                  {'post': comment.post, 'comment': comment,
                   'confirm_delete': True})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/create.html', {'post': post})


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = CustomUserChangeForm(instance=request.user)
    return render(request, 'blog/edit_profile.html', {'form': form})


class CustomPasswordChangeView(PasswordChangeView):
    """Смена пароля с отправкой письма (если email указан)."""

    template_name = 'registration/password_change_form.html'
    success_url = reverse_lazy('password_change_done')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.email:
            send_mail(
                subject='Password',
                message='Ваш пароль успешно изменён.',
                from_email='no-reply@django.com',
                recipient_list=[user.email],
                fail_silently=True
            )
        return response
