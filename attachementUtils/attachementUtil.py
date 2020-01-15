from tbDAO import AttachementHeader
from tbDAO import Base
from datetime import datetime
from common import REQUEST_HEADERS
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
from requests.adapters import HTTPAdapter
import os

MAX_RETRY = 5

proxies = {}

if os.environ.get("http_proxy"):
    proxies["http"] = os.environ.get("http_proxy")

if os.environ.get("https_proxy"):
    proxies["https"] = os.environ.get("https_proxy")

req = requests.Session()
if proxies:
    req.proxies.update(proxies)
httpAdapter = HTTPAdapter(max_retries=MAX_RETRY)

req.mount('http://', httpAdapter)
req.mount('https://', httpAdapter)


def makeEmptyAttachementHeader(link: str, pid: str) -> AttachementHeader:
    att = AttachementHeader()
    att.mod_date = datetime.now()
    att.link = link
    att.pid = pid
    return att


def downloadAttachement(
        att: AttachementHeader,
        attachementBasePath="data/attachements/"):
    import re
    import os.path
    from pathlib import Path
    # from common import ATTACHEMENT_BASE_PATH
    # from common import ATTACHEMENT_OUT_BASE_PATH

    existFlag = False
    subPath = att.path
    if subPath is not None:
        subPath = Path(attachementBasePath).joinpath(subPath)
        if os.path.isfile(subPath):
            existFlag = True

    if not existFlag:
        downUrl = att.link
        # downUrl = 'http://dl1.subhd.com/sub/2019/03/155343934746869.zip'
        if not downUrl:
            return None
        localUrl = re.sub(r'[ <>*?|:\\\t"]', '_', str(downUrl))
        parts = Path(localUrl).parts[1:]  # cut http[s] and host
        subPath = Path("")
        for part in parts:
            subPath = subPath.joinpath(part)
        fullPath = Path(attachementBasePath).joinpath(subPath)
        os.makedirs(fullPath.parent, mode=0o755, exist_ok=True)

        ret = req.get(downUrl, headers=REQUEST_HEADERS, timeout=(30, 300))
        att.status = int(ret.status_code)

        if att.status and att.status < 400:
            with open(fullPath, "wb") as code:
                code.write(ret.content)

        att.path = subPath.as_posix()
        att.title = subPath.name
        att.downloaded = datetime.now()
        att.mod_date = datetime.now()
        logging.info("Download {} to {}".format(att.link, att.path))

    return att


def fetchAttAll(dbUrl, attrfilter=None, fatchSize=200, nbMaxBlocked=10, attachementBasePath="data/attachements/"):
    import random

    engine = create_engine(dbUrl)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    nbResOld = -1
    nbBlocked = 0

    processBegin = datetime.now()

    if attrfilter is None:
        attrfilter = ((AttachementHeader.mod_date < processBegin) &
                      ((AttachementHeader.status.is_(None)) | (AttachementHeader.status.between(400, 999))))

    while True:
        try:
            start = datetime.now().timestamp()
            session = Session()
            # from sqlalchemy.sql import exists, or_
            results = session.query(AttachementHeader) \
                .filter(attrfilter) \
                .limit(fatchSize).all()
            session.expunge_all()
            session.commit()

            nbRes = len(results)
            if nbResOld == nbRes and nbRes != fatchSize:
                nbBlocked += 1
            else:
                nbBlocked = 0

            if len(results) == 0 or nbBlocked > nbMaxBlocked:
                break

            index = random.randrange(len(results))
            header: AttachementHeader = results[index]

            logging.info("Got {} subs took {:.3f}(sec) old is {} blocked {}, select nb {}: {} - {}".format(
                nbRes, datetime.now(
                ).timestamp() - start, nbResOld, nbBlocked,
                index, header.pid, header.link))
            nbResOld = nbRes

            try:
                header = downloadAttachement(header, attachementBasePath=attachementBasePath)
            except Exception as e:
                from common import STATUS_UNKNOW_ERROR
                header.status = STATUS_UNKNOW_ERROR
                header.comment = str(e)
                header.mod_date = datetime.now()
                logging.warn("{} {} {}".format(header.link,header.status,header.comment))

            session = Session()
            if header:
                if not header.status:
                    header.status = STATUS_UNKNOW_ERROR
                session.merge(header)
            session.commit()
        except Exception as e:
            print("Error download thread for {}".format(e))


if __name__ == '__main__':
    import argparse
    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.basicConfig(format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logging.getLogger("chardet.charsetprober").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    parser = argparse.ArgumentParser()

    parser.add_argument('-d', "--db",
                        dest='db',
                        help="path to db",
                        required=False,
                        type=str,
                        default='sqlite:///data/tieba.baidu.com.db')

    parser.add_argument('-p', "--path",
                        dest='path',
                        help="path to save attachements",
                        required=False,
                        type=str,
                        default='data/attachements/')

    args = parser.parse_args()

    fetchAttAll(dbUrl=args.db, attachementBasePath=args.path)
    pass
