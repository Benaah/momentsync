# from azure.storage import CloudStorageAccount
# from django.apps import AppConfig
# from . import config
# from common.utils import dbstorage
#
#
# class Configuration(AppConfig):
#     def ready(self):
#         #import hashlib
#         #    print(hashlib.md5(b"hello").hexdigest())
#         account_name = config.STORAGE_ACCOUNT_NAME
#         account_key = config.STORAGE_ACCOUNT_KEY
#         account = CloudStorageAccount(account_name, account_key)
#         db = account.create_table_service()
#         dbstorage.initialize(db)
#
#         pass # startup code here