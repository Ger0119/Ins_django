from django.db import models

# Create your models here.
class Insight(models.Model):
    follower = models.IntegerField('Follower')
    follows = models.IntegerField('Follows')
    label = models.CharField('Created Date',max_length=100)

    def __str__(self):
        return str(self.label)

class Post(models.Model):
    like = models.IntegerField('Like')
    comment = models.IntegerField('Comment')
    count = models.IntegerField('Post Count')
    label = models.CharField('Post Date',max_length=100)

    def __str__(self):
        return str(self.label)

class HashTag(models.Model):
    tag = models.CharField('Hash Tag',max_length=100)
    count = models.IntegerField('Post Count')
    label = models.CharField('Post Date',max_length=100)

    def __str__(self):
        return str(self.label) + ':' + str(self.tag)
