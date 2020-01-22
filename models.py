import uuid
from django.db import models

# Note: there's a lot more that should go into these models in 'real life'
# such as help messages for forms/admins, __str__() methods, unique_together
# constraints etc. but for the purposes of this exercise I didn't bother
# with all of that since I'm not using the admin and have limited time.

# Dimensions

class Campaign(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Audience(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    campaign = models.ForeignKey(Campaign, models.CASCADE)
    state = models.CharField(max_length=2)
    hair_color = models.CharField(max_length=20)
    age_min = models.PositiveSmallIntegerField()
    age_max = models.PositiveSmallIntegerField()


class AdType(models.Model):
    id = models.CharField(max_length=10, primary_key=True, editable=False)


class Source(models.Model):
    id = models.CharField(max_length=1, primary_key=True, editable=False)


class Action(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)


class Date(models.Model):
    id = models.DateField(primary_key=True, editable=False)


# Fact tables

#NOTE: there are duplicate campaign/audience keys.. this table could be 'flattened'
# and use unique_together on campaign, audience. But, it depends on implementation
# really. If this was 'real life', would this be a table that gets appended to often
# and duplicates don't matter..... or would we enforce that campaign/audience is
# unique together and that the impressions column is updated instead?
class Impression(models.Model):
    campaign = models.ForeignKey(Campaign, models.CASCADE)
    audience = models.ForeignKey(Audience, models.CASCADE)
    impressions = models.IntegerField()


class Spend(models.Model):
    id = models.CharField(max_length=60, primary_key=True, editable=False)
    campaign = models.ForeignKey(Campaign, models.CASCADE)
    audience = models.ForeignKey(Audience, models.CASCADE)
    ad_type = models.ForeignKey(AdType, models.CASCADE)
    date = models.ForeignKey(Date, models.CASCADE)
    spend = models.DecimalField(max_digits=5, decimal_places=2)


class Stat(models.Model):
    spend = models.ForeignKey(Spend, models.CASCADE)
    campaign = models.ForeignKey(Campaign, models.CASCADE)
    audience = models.ForeignKey(Audience, models.CASCADE)
    ad_type = models.ForeignKey(AdType, models.CASCADE)
    date = models.ForeignKey(Date, models.CASCADE)
    source = models.ForeignKey(Source, models.CASCADE)
    action = models.ForeignKey(Action, models.CASCADE)
    count = models.IntegerField()
