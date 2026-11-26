# users/signals.py
import os
from django.conf import settings
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from .models import PriceRequest


def _remove_empty_dirs(file_path):
    """
    Удаляет пустые папки вверх по дереву, начиная от папки файла,
    но НЕ выше MEDIA_ROOT/price_requests/.
    Безопасно: если папка не пустая — останавливается.
    """
    if not file_path:
        return

    # Абсолютный путь к папке файла
    folder = os.path.dirname(os.path.join(settings.MEDIA_ROOT, file_path))

    # Граница, выше которой не поднимаемся
    stop_at = os.path.join(settings.MEDIA_ROOT, 'price_requests')

    while folder and folder.startswith(stop_at) and folder != stop_at:
        try:
            os.rmdir(folder)   # удалит только если папка пустая
        except OSError:
            break              # не пустая или нет прав — стоп
        folder = os.path.dirname(folder)


@receiver(pre_save, sender=PriceRequest)
def delete_old_attachment_on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = PriceRequest.objects.get(pk=instance.pk)
    except PriceRequest.DoesNotExist:
        return

    old_file = old.attachment
    new_file = instance.attachment

    if not old_file:
        return

    old_path = old_file.name  # сохраняем ДО delete()

    if new_file and old_file.name != new_file.name:
        old_file.delete(save=False)
        _remove_empty_dirs(old_path)
    elif not new_file:
        old_file.delete(save=False)
        _remove_empty_dirs(old_path)


@receiver(post_delete, sender=PriceRequest)
def delete_attachment_on_delete(sender, instance, **kwargs):
    if instance.attachment:
        old_path = instance.attachment.name
        instance.attachment.delete(save=False)
        _remove_empty_dirs(old_path)