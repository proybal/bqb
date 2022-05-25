from django.db import models


class News(models.Model):
    source = models.URLField()
    title = models.CharField(max_length=20)
    cover = models.ImageField(upload_to='images/')
    url = models.URLField()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'news'
        # Add verbose name
        verbose_name = 'New' # dumb i know but otherwise it displays 'Newss'