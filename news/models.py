from django.db import models

REGION_CHOICES = (
    ('Albuquerque', 'Albuquerque'),
    ('New Mexico', 'New Mexico'),
    ('Politics', 'Politics'),
    ('Northern', 'Northern'),
    ('Central', 'Central'),
    ('Southern', 'Southern'),
    ('Eastern', 'Eastern'),
    ('Western', 'Western'),
    ('Northwestern', 'Northwestern'),
    ('Northeastern', 'Northeastern'),
    ('Southern', 'Southern'),
    ('Southwestern', 'Southwestern'),
    ('Southeastern', 'Southeastern'),
)

COUNTY_CHOICES = [
    ('Bernalillo', 'Bernalillo'),
    ('Catron', 'Catron'),
    ('Chavez', 'Chavez'),
    ('Cibola', 'Cibola'),
    ('Colfax', 'Colfax'),
    ('Curry', 'Curry'),
    ('De_Baca', 'De_Baca'),
    ('Dona_Anna', 'Dona_Anna'),
    ('Eddy', 'Eddy'),
    ('Grant', 'Grant'),
    ('Guadalupe', 'Guadalupe'),
    ('Harding', 'Harding'),
    ('Lea', 'Lea'),
    ('Lincoln', 'Lincoln'),
    ('Los_Alamos', 'Los_Alamos'),
    ('Luna', 'Luna'),
    ('McKinley', 'McKinley'),
    ('Mora', 'Mora'),
    ('Otero', 'Otero'),
    ('Quay', 'Quay'),
    ('Rio_Arriba', 'Rio_Arriba'),
    ('Rio_Rancho', 'Rio_Rancho'),
    ('Roosevelt', 'Roosevelt'),
    ('San_Juan', 'San_Juan'),
    ('San_Miguel', 'San_Miguel'),
    ('Sandoval', 'Sandoval'),
    ('Santa_Fe', 'Santa_Fe'),
    ('Sierra', 'Sierra'),
    ('Socorro', 'Socorro'),
    ('Taos', 'Taos'),
    ('Torrance', 'Torrance'),
    ('Union', 'Union'),
    ('Valencia', 'Valencia')]

CITY_CHOICES = [('Albuquerque', 'Albuquerque'),
                ('Alamagordo', 'Alamagordo'),
                ('Artesia', 'Artesia'),
                ('Belen', 'Belen'),
                ('Carlsbad', 'Carlsbad'),
                ('Clovis', 'Clovis'),
                ('Gallup', 'Gallup'),
                ('Grants', 'Grants'),
                ('Edgewood', 'Edgewood'),
                ('Espanola', 'Espanola'),
                ('Farmington', 'Farmington'),
                ('Gallup', 'Gallup'),
                ('Hobbs', 'Hobbs'),
                ('Las Cruces', 'Las_Cruces'),
                ('Las_Vegas', 'Las_Vegas'),
                ('Los_Alamos', 'Los_Alamos'),
                ('Portales', 'Portales'),
                ('Rio_Rancho', 'Rio_Rancho'),
                ('Roswell', 'Roswell'),
                ('Santa_Fe', 'Santa_Fe'),
                ('Silver_City', 'Silver_City'),
                ('Socorro', 'Socorro'),
                ('Taos', 'Taos'),
                ('T_or_C', 'T_or_C')]


class Counties(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'county'
        # Add verbose name
        verbose_name = 'County'
        verbose_name_plural = 'Counties'


class Cities(models.Model):
    name = models.CharField(max_length=20)
    county = models.ForeignKey(Counties, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'city'
        # Add verbose name
        verbose_name = 'City'
        verbose_name_plural = 'Cities'


class Region(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'region'



class News(models.Model):
    source = models.URLField()
    title = models.CharField(max_length=50)
    cover = models.ImageField(upload_to='images/')
    feed_url = models.URLField()
    city = models.ForeignKey(Cities, null=True, on_delete=models.SET_NULL)
    county = models.ForeignKey(Counties, null=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, on_delete=models.SET_NULL)
    function = models.CharField(max_length=20)
    published = models.BooleanField(default=False)
    selenium = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'news'
        # Add verbose name
        verbose_name = 'New'  # dumb i know but otherwise it displays 'Newss'
