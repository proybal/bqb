# slideshow/models.py
from django.db import models


class Slideshow(models.Model):
    title = models.TextField()
    cover = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.title
