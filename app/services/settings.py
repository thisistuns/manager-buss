"""
Dịch vụ cài đặt hệ thống
Quản lý việc đọc, cập nhật và bộ nhớ đệm cấu hình hệ thống
"""
from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Setting
import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """Lớp dịch vụ cài đặt hệ thống"""

    def __init__(self):
        self._cache: Dict[str, str] = {}

    async def get_setting(self, session: AsyncSession, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Lấy một mục cấu hình

        Args:
            session: Phiên làm việc với cơ sở dữ liệu
            key: Khóa cấu hình
            default: Giá trị mặc định

        Returns:
            Giá trị cấu hình, nếu không tồn tại sẽ trả về giá trị mặc định
        """
        # Lấy từ bộ nhớ đệm trước
        if key in self._cache:
            return self._cache[key]

        # Lấy từ cơ sở dữ liệu
        result = await session.execute(
            select(Setting).where(Setting.key == key)
        )
        setting = result.scalar_one_or_none()

        if setting:
            self._cache[key] = setting.value
            return setting.value

        return default

    async def get_all_settings(self, session: AsyncSession) -> Dict[str, str]:
        """
        Lấy tất cả các mục cấu hình

        Args:
            session: Phiên làm việc với cơ sở dữ liệu

        Returns:
            Từ điển các mục cấu hình
        """
        result = await session.execute(select(Setting))
        settings = result.scalars().all()

        settings_dict = {s.key: s.value for s in settings}
        self._cache.update(settings_dict)

        return settings_dict

    async def update_setting(self, session: AsyncSession, key: str, value: str) -> bool:
        """
        Cập nhật một mục cấu hình

        Args:
            session: Phiên làm việc với cơ sở dữ liệu
            key: Khóa cấu hình
            value: Giá trị cấu hình

        Returns:
            Có cập nhật thành công hay không
        """
        try:
            result = await session.execute(
                select(Setting).where(Setting.key == key)
            )
            setting = result.scalar_one_or_none()

            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                session.add(setting)

            await session.commit()

            # Cập nhật bộ nhớ đệm
            self._cache[key] = value

            logger.info(f"Cấu hình {key} đã được cập nhật")
            return True

        except Exception as e:
            logger.error(f"Cập nhật cấu hình {key} thất bại: {e}")
            await session.rollback()
            return False

    async def update_settings(self, session: AsyncSession, settings: Dict[str, str]) -> bool:
        """
        Cập nhật hàng loạt các mục cấu hình

        Args:
            session: Phiên làm việc với cơ sở dữ liệu
            settings: Từ điển các mục cấu hình

        Returns:
            Có cập nhật thành công hay không
        """
        try:
            for key, value in settings.items():
                result = await session.execute(
                    select(Setting).where(Setting.key == key)
                )
                setting = result.scalar_one_or_none()

                if setting:
                    setting.value = value
                else:
                    setting = Setting(key=key, value=value)
                    session.add(setting)

            await session.commit()

            # Cập nhật bộ nhớ đệm
            self._cache.update(settings)

            logger.info(f"Đã cập nhật hàng loạt {len(settings)} mục cấu hình")
            return True

        except Exception as e:
            logger.error(f"Cập nhật hàng loạt cấu hình thất bại: {e}")
            await session.rollback()
            return False

    def clear_cache(self):
        """Xóa sạch bộ nhớ đệm"""
        self._cache.clear()
        logger.info("Bộ nhớ đệm cấu hình đã được xóa")

    async def get_proxy_config(self, session: AsyncSession) -> Dict[str, str]:
        """
        Lấy cấu hình proxy

        Returns:
            Từ điển cấu hình proxy
        """
        proxy_enabled = await self.get_setting(session, "proxy_enabled", "false")
        proxy = await self.get_setting(session, "proxy", "")

        return {
            "enabled": str(proxy_enabled).lower() == "true",
            "proxy": proxy
        }

    async def update_proxy_config(
        self,
        session: AsyncSession,
        enabled: bool,
        proxy: str = ""
    ) -> bool:
        """
        Cập nhật cấu hình proxy

        Args:
            session: Phiên làm việc với cơ sở dữ liệu
            enabled: Có bật proxy hay không
            proxy: Địa chỉ proxy (định dạng: http://host:port hoặc socks5://host:port)

        Returns:
            Có cập nhật thành công hay không
        """
        settings = {
            "proxy_enabled": str(enabled).lower(),
            "proxy": proxy
        }

        return await self.update_settings(session, settings)

    async def get_log_level(self, session: AsyncSession) -> str:
        """
        Lấy cấp độ log

        Returns:
            Cấp độ log
        """
        return await self.get_setting(session, "log_level", "INFO")

    async def update_log_level(self, session: AsyncSession, level: str) -> bool:
        """
        Cập nhật cấp độ log

        Args:
            session: Phiên làm việc với cơ sở dữ liệu
            level: Cấp độ log (DEBUG/INFO/WARNING/ERROR/CRITICAL)

        Returns:
            Có cập nhật thành công hay không
        """
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level.upper() not in valid_levels:
            logger.error(f"Cấp độ log không hợp lệ: {level}")
            return False

        success = await self.update_setting(session, "log_level", level.upper())

        if success:
            # Cập nhật động cấp độ log
            logging.getLogger().setLevel(level.upper())
            logger.info(f"Cấp độ log đã được cập nhật thành: {level.upper()}")

        return success


# Tạo instance toàn cục
settings_service = SettingsService()
