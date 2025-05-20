from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class BaseModel(models.Model):
    is_published = models.BooleanField(
        _("Опубликовано"),
        default=True,
        help_text=_("Снимите галочку, чтобы скрыть публикацию."),
    )
    created_at = models.DateTimeField(_("Добавлено"), auto_now_add=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    title = models.CharField(_("Заголовок"), max_length=256)
    description = models.TextField(_("Описание"))
    slug = models.SlugField(
        _("Идентификатор"),
        unique=True,
        help_text=_(
            "Идентификатор страницы для URL; разрешены символы латиницы, "
            "цифры, дефис и подчёркивание."
        ),
    )

    class Meta:
        verbose_name = _("категория")
        verbose_name_plural = _("Категории")

    def __str__(self):
        return self.title


class Location(BaseModel):
    name = models.CharField(_("Название места"), max_length=256)

    class Meta:
        verbose_name = _("местоположение")
        verbose_name_plural = _("Местоположения")

    def __str__(self):
        return self.name


class Post(BaseModel):
    title = models.CharField(_("Заголовок"), max_length=256)
    text = models.TextField(_("Текст"))
    pub_date = models.DateTimeField(
        _("Дата и время публикации"),
        help_text=_(
            "Если установить дату и время в будущем —"
            "можно делать отложенные публикации."
        ),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name=_("Автор публикации"))
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name=_("Местоположение")
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        verbose_name=_("Категория")
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )

    @property
    def comment_count(self):
        return self.comments.count()

    class Meta:
        verbose_name = _("публикация")
        verbose_name_plural = _("Публикации")
        ordering = ["-pub_date"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Комментарий от {self.author}'
