import re
import csv
import json
import argparse
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db import models
from tracer_assignment.models import *

# This management script loads the data from the CSV files into the database
# It uses bulk load (bulk_create) and natural keys for speed as calling the ORM .save() method
# on this many records is significantly slower than bulk_create(). It also sets up foreign key
# relations and handles dependencies (i.e. inserts records in the correct order so that dependencies
# are in place before FKs are made.

# Sample use to load the CSVs after manage.py migrate has been run:
# manage.py import_csv_data impressions tracer_source1.csv
# manage.py import_csv_data stats tracer_source2.csv

# the --delete flag can be used as well to clear all of the assignment tables prior to reloading
# the data. This is useful for development/debugging/testing

class BulkLoader:

    orm_cls = None
    requires = []
    index_key = None

    def __init__(self, requires_loaders, logger=None):

        self.requires_loaders = requires_loaders

        self.orm_obj_cache = {} if self.index_key else []
        self.logger = logger

    def write(self, msg):
        # This is so this class plays nicely with management commands where the
        # preferred method of output is using Command.stdout.write() rather than print()
        if self.logger:
            self.logger.stdout.write(msg)
        else:
            print(msg)

    def save(self, visited_set=None):

        visited_set = set() if visited_set is None else visited_set

        visited_set.add(self.orm_cls)

        for bulk_loader in self.requires:
            if bulk_loader.orm_cls in visited_set:
                continue

            bulk_loader_inst = self.requires_loaders[bulk_loader]
            bulk_loader_inst.save(visited_set)

        insert_list = self.orm_obj_cache.values() if self.index_key else self.orm_obj_cache
        if self.orm_cls._meta.verbose_name_plural.title() == 'Spend':
            check_set = set()
            for x in insert_list:
                if x.id in check_set:
                    print(x.id)
                    assert False
                check_set.add(x.id)
        if insert_list:
            self.write('Saving new {} ...'.format(self.orm_cls._meta.verbose_name_plural.title()))
            self.orm_cls.objects.bulk_create(insert_list)

    def get_key(self, csv_row):
        return csv_row[self.index_key]

    def get_row_obj(self, csv_row):
        return self.orm_cls(pk = self.get_key(csv_row))

    def cache_row(self, csv_row):
        if self.index_key:
            key = self.get_key(csv_row)

            if isinstance(key, models.Model):
                return key # get_key already checked for existing object and fetched it - no need to fetch it again as this is a model instance

            try:
                orm_obj = self.orm_cls.objects.get(pk = key)
                self.write('{} exists: {}'.format(self.orm_cls._meta.verbose_name.title(), key))
            except self.orm_cls.DoesNotExist:
                if key not in self.orm_obj_cache:
                    self.write('Will create new {}: {}'.format(self.orm_cls._meta.verbose_name.title(), key))
                orm_obj = self.orm_obj_cache.setdefault(key, self.get_row_obj(csv_row))
        else:
            orm_obj = self.get_row_obj(csv_row)
            if type(orm_obj) is list:
                self.orm_obj_cache.extend(orm_obj)
            else:
                self.orm_obj_cache.append(orm_obj)
        return orm_obj

    @classmethod
    def load_data(cls, file_obj, logger=None):

        requires_loaders = {}

        require_stack = cls.requires[:] # use a copy so we don't mutate the class instance when we pop

        walk = require_stack.pop()

        while walk:
            requires_loaders.setdefault(walk, walk(requires_loaders, logger))
            require_stack.extend(walk.requires)
            walk = require_stack.pop() if require_stack else []

        inst = cls(requires_loaders, logger)

        with file_obj as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                inst.cache_row(row)

        inst.save()


class CampaignBulkLoader(BulkLoader):
    orm_cls = Campaign
    index_key = 'campaign_id'


class AudienceBulkLoader(BulkLoader):
    orm_cls = Audience
    requires = [CampaignBulkLoader]
    index_key = True

    # Regex pattern to extract components from audience string as match groups
    audience_pattern = r'^(?P<state>[A-Z]{2})_(?P<color>[a-z]+)_(?P<min_age>\d+)-(?P<max_age>\d+)$'

    # Compile regex once here for efficiency
    audience_matcher = re.compile(audience_pattern)

    def get_key(self, csv_row):
        if 'audience' in csv_row:
            return csv_row['audience']
        else:
            return self.orm_cls.objects.get(campaign=csv_row['campaign_id'])

    def get_row_obj(self, csv_row):
        #TODO better handling in case match fails (edge case: corrupt CSV data)
        match = self.audience_matcher.match(csv_row['audience'])

        orm_obj = self.orm_cls(
            pk = csv_row['audience'],
            campaign = self.requires_loaders[CampaignBulkLoader].cache_row(csv_row),
            state = match.group('state'),
            hair_color = match.group('color'),
            age_min = match.group('min_age'),
            age_max = match.group('max_age'),
        )

        return orm_obj


class ImpressionBulkLoader(BulkLoader):
    orm_cls = Impression
    requires = [CampaignBulkLoader, AudienceBulkLoader]

    def get_row_obj(self, csv_row):

        orm_obj = self.orm_cls(
            campaign = self.requires_loaders[CampaignBulkLoader].cache_row(csv_row),
            audience = self.requires_loaders[AudienceBulkLoader].cache_row(csv_row),
            impressions = csv_row['impressions']
        )

        return orm_obj


class AdTypeBulkLoader(BulkLoader):
    orm_cls = AdType
    index_key = 'ad_type'


class DateBulkLoader(BulkLoader):
    orm_cls = Date
    index_key = 'date'


class SourceBulkLoader(BulkLoader):
    orm_cls = Source
    index_key = True

    def get_key(self, json_val):
        return json_val


class ActionBulkLoader(BulkLoader):
    orm_cls = Action
    index_key = True

    def get_key(self, json_val):
        return json_val


class SpendBulkLoader(BulkLoader):
    orm_cls = Spend
    requires = [CampaignBulkLoader, AudienceBulkLoader, AdTypeBulkLoader, DateBulkLoader]
    index_key = True

    def get_key(self, csv_row):
        return '{}_{}_{}'.format(csv_row['campaign_id'], csv_row['ad_type'], csv_row['date'])

    def get_row_obj(self, csv_row):

        orm_obj = self.orm_cls(
            pk = self.get_key(csv_row),
            campaign = self.requires_loaders[CampaignBulkLoader].cache_row(csv_row),
            audience = self.requires_loaders[AudienceBulkLoader].cache_row(csv_row),
            ad_type = self.requires_loaders[AdTypeBulkLoader].cache_row(csv_row),
            date = self.requires_loaders[DateBulkLoader].cache_row(csv_row),
            spend = csv_row['spend']
        )
        return orm_obj


class StatBulkLoader(BulkLoader):
    orm_cls = Stat
    requires = [CampaignBulkLoader, AudienceBulkLoader, SourceBulkLoader, AdTypeBulkLoader, ActionBulkLoader, DateBulkLoader, SpendBulkLoader]

    def get_row_obj(self, csv_row):
        orm_objs = []

        campaign = self.requires_loaders[CampaignBulkLoader].cache_row(csv_row)
        audience = self.requires_loaders[AudienceBulkLoader].cache_row(csv_row)
        ad_type = self.requires_loaders[AdTypeBulkLoader].cache_row(csv_row)
        spend = self.requires_loaders[SpendBulkLoader].cache_row(csv_row)
        date = self.requires_loaders[DateBulkLoader].cache_row(csv_row)

        action_data = json.loads(csv_row['actions'])

        for action_dict in action_data:
            stat_action = action_dict.pop('action')
            action = self.requires_loaders[ActionBulkLoader].cache_row(stat_action)

            for k, v in action_dict.items():
                orm_obj = self.orm_cls(
                    spend = spend,
                    campaign = campaign,
                    audience = audience,
                    ad_type = ad_type,
                    date = date,
                    source = self.requires_loaders[SourceBulkLoader].cache_row(k),
                    action = action,
                    count = v
                )
                orm_objs.append(orm_obj)

        return orm_objs


CSV_TYPE_LOADERS = {
    'impressions': ImpressionBulkLoader,
    'stats': StatBulkLoader,
}


class Command(BaseCommand):
    help = 'Loads data from CSVs into relevant tables'

    def add_arguments(self, parser):
        parser.add_argument('type', choices = CSV_TYPE_LOADERS.keys())
        parser.add_argument('file', type = argparse.FileType('r'))

        # delete all existing records before re-loading
        parser.add_argument('--delete', default=False, action='store_true')

    def delete(self):
        cursor = connection.cursor()
        self.stdout.write('Deleting all existing data ...')

        # use raw SQL here - it's MUCH faster in bulk than the ORM delete() method
        for t_name in ('impression', 'stat', 'spend', 'adtype', 'source', 'action', 'date', 'audience', 'campaign'):
            cursor.execute("DELETE FROM assignment_{}".format(t_name))


    def handle(self, *args, **options):

        if options['delete']:
            self.delete()


        csv_type = options['type']

        loader = CSV_TYPE_LOADERS[csv_type]

        loader.load_data(options['file'], self)
