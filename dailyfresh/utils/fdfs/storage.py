from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from dailyfresh import settings

class FDFSStorage(Storage):

    def __init__(self):
        try:
            self.FDFS_URL = settings.FDFS_URL
            self.FDFS_CLIENT_CONF = settings.FDFS_CLIENT_CONF
        except:

            raise Exception("请在settings下配置 FDFS_URL：nginx服务器地址,FDFS_CLIENT_CONF：fdfs使用的client.conf路径")


    def _open(self,name,mode="wb"):
        pass

    def _save(self,name,content):

        # 创建fdfs对象
        client = Fdfs_client(self.FDFS_CLIENT_CONF)
        # 将文件内容上传
        res = client.upload_by_buffer(content.read())
        # 判断是否上传成功
        if res.get("Status") != "Upload successed.":

            raise Exception("上传失败")

        return res.get('Remote file_id')

    def exists(self, name):

        return False

    def url(self, name):

        return self.FDFS_URL +name






































