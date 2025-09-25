import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from open_webui.internal.db import Base
from open_webui.models.media_library import (
    MediaAsset,
    MediaFolder,
    MediaLibrarySettings,
)


def create_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_media_folder_crud():
    session = create_session()
    try:
        folder = MediaFolder(
            id="folder-1",
            owner_id="user-1",
            visibility_scope="user",
            name="My Folder",
            sort_order=0,
        )
        session.add(folder)
        session.commit()

        saved = session.query(MediaFolder).filter_by(id="folder-1").first()
        assert saved is not None
        assert saved.name == "My Folder"

        saved.name = "Renamed"
        session.commit()

        updated = session.query(MediaFolder).filter_by(id="folder-1").first()
        assert updated.name == "Renamed"
    finally:
        session.close()


def test_media_asset_persistence():
    session = create_session()
    try:
        folder = MediaFolder(
            id="folder-asset",
            owner_id="user-asset",
            visibility_scope="user",
            name="Assets",
            sort_order=0,
        )
        session.add(folder)

        asset = MediaAsset(
            id="asset-1",
            file_id="file-1",
            visibility_scope="user",
            owner_id="user-asset",
            display_name="Generated Image",
            media_type="image",
            folder_id="folder-asset",
        )
        session.add(asset)
        session.commit()

        saved = session.query(MediaAsset).filter_by(id="asset-1").first()
        assert saved is not None
        assert saved.display_name == "Generated Image"
        assert saved.folder_id == "folder-asset"

        session.delete(saved)
        session.commit()
        assert session.query(MediaAsset).filter_by(id="asset-1").first() is None
    finally:
        session.close()


def test_media_library_settings_defaults():
    session = create_session()
    try:
        settings = MediaLibrarySettings(
            id="default",
            enable_group_sharing=False,
            allow_bulk_download=True,
            default_visibility="user",
        )
        session.add(settings)
        session.commit()

        saved = session.query(MediaLibrarySettings).filter_by(id="default").first()
        assert saved is not None
        assert saved.allow_bulk_download is True
        assert saved.default_visibility == "user"
    finally:
        session.close()
