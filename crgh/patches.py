"""Runtime monkey-patches for third-party libraries."""

import logging
import pickle
import sqlite3

logger = logging.getLogger(__name__)


def apply_perceval_archive_fix():
    """Patch Archive.store to silently skip duplicate entries.

    Perceval's Archive.store uses a plain INSERT which raises an ArchiveError
    when the same hashcode (URI+payload+headers) is stored a second time. This
    happens when an existing archive file is reused across runs, or when the
    same URL is requested more than once in a single run.

    The fix replaces the INSERT with INSERT OR IGNORE so that a duplicate write
    is a no-op rather than a hard error.
    """
    from perceval.archive import Archive

    original_store = Archive.store

    def patched_store(self, uri, payload, headers, data):
        hashcode = Archive.make_hashcode(uri, payload, headers)
        payload_dump = pickle.dumps(payload, 0)
        headers_dump = pickle.dumps(headers, 0)
        data_dump = pickle.dumps(data, 0)

        logger.debug(
            "Archiving %s with %s %s %s in %s",
            hashcode, uri, payload, headers, self.archive_path,
        )

        try:
            cursor = self._db.cursor()
            insert_stmt = (
                "INSERT OR IGNORE INTO " + Archive.ARCHIVE_TABLE + " ("
                "id, hashcode, uri, payload, headers, data) "
                "VALUES(?,?,?,?,?,?)"
            )
            cursor.execute(insert_stmt, (None, hashcode, uri,
                                         payload_dump, headers_dump, data_dump))
            self._db.commit()
            cursor.close()
        except sqlite3.DatabaseError as e:
            from perceval.errors import ArchiveError
            msg = "data storage error; cause: %s" % str(e)
            raise ArchiveError(cause=msg)

        logger.debug("%s data archived in %s", hashcode, self.archive_path)

    Archive.store = patched_store
    logger.debug("perceval Archive.store patched to ignore duplicate entries")


def apply_perceval_client_fetch_fix():
    """
    Patches perceval.client.Client to ignore ``from_archive`` and always
    attempt to fetch from the cache before making API calls.
    """
    from perceval.client import HttpClient
    from perceval.archive import ArchiveError

    original_fetch = HttpClient.fetch

    GET = "GET"

    def patched_fetch(self, url, payload=None, headers=None, method=GET, stream=False, auth=None):
        """Fetch the data from a given URL.

        :param url: link to the resource
        :param payload: payload of the request
        :param headers: headers of the request
        :param method: type of request call (GET or POST)
        :param stream: defer downloading the response body until the response content is available
        :param auth: auth of the request

        :returns a response object
        """
        if self.archive is not None:
            try:
                response = self._fetch_from_archive(url, payload, headers)
            except ArchiveError:
                response = None

            if response is not None:
                return response
            
        response = self._fetch_from_remote(url, payload, headers, method, stream, auth)

        return response

    HttpClient.fetch = patched_fetch
    logger.debug("perceval HttpClient.fetch patched to ignore from_archive flag")
