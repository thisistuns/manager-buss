"""
Dịch vụ bảo hành
Xử lý tra cứu và xác minh bảo hành cho người dùng
"""
import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import RedemptionCode, RedemptionRecord, Team
from app.utils.time_utils import get_now

logger = logging.getLogger(__name__)

# Từ điển giới hạn tần suất toàn cục: {(type, key): last_time}
# type: 'email' hoặc 'code'
_query_rate_limit = {}


class WarrantyService:
    """Lớp dịch vụ bảo hành"""

    def __init__(self):
        """Khởi tạo dịch vụ bảo hành"""
        from app.services.team import TeamService
        self.team_service = TeamService()

    async def check_warranty_status(
        self,
        db_session: AsyncSession,
        email: Optional[str] = None,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Kiểm tra trạng thái bảo hành của người dùng

        Args:
            db_session: Phiên làm việc với cơ sở dữ liệu
            email: Email người dùng
            code: Mã đổi

        Returns:
            Từ điển kết quả, bao gồm success, has_warranty, warranty_valid, warranty_expires_at, 
            banned_teams, can_reuse, original_code, error
        """
        try:
            if not email and not code:
                return {
                    "success": False,
                    "error": "Bắt buộc phải cung cấp email hoặc mã đổi"
                }

            # 0. Giới hạn tần suất (mỗi email hoặc mỗi mã chỉ được tra cứu 30 giây một lần)
            now = datetime.now()
            limit_key = ("email", email) if email else ("code", code)
            last_time = _query_rate_limit.get(limit_key)
            if last_time and (now - last_time).total_seconds() < 30:
                wait_time = int(30 - (now - last_time).total_seconds())
                return {
                    "success": False,
                    "error": f"Tra cứu quá thường xuyên, vui lòng thử lại sau {wait_time} giây"
                }
            _query_rate_limit[limit_key] = now

            # 1. Tìm bản ghi đổi và Team, Code liên quan
            records_data = []

            if code:
                # Tìm tất cả bản ghi liên quan thông qua mã đổi
                stmt = (
                    select(RedemptionRecord, RedemptionCode, Team)
                    .options(selectinload(RedemptionRecord.redemption_code), selectinload(RedemptionRecord.team))
                    .join(RedemptionCode, RedemptionRecord.code == RedemptionCode.code)
                    .join(Team, RedemptionRecord.team_id == Team.id)
                    .where(RedemptionCode.code == code)
                    .order_by(RedemptionRecord.redeemed_at.desc())
                )
                result = await db_session.execute(stmt)
                first_record = result.first()
                if first_record:
                    records_data = [first_record]
                else:
                    records_data = []

                # Nếu không có bản ghi, có thể là mã chưa được sử dụng hoặc không tồn tại
                if not records_data:
                    stmt = select(RedemptionCode).where(RedemptionCode.code == code)
                    result = await db_session.execute(stmt)
                    redemption_code_obj = result.scalar_one_or_none()
                    
                    if not redemption_code_obj:
                        return {
                            "success": True,
                            "has_warranty": False,
                            "warranty_valid": False,
                            "warranty_expires_at": None,
                            "banned_teams": [],
                            "can_reuse": False,
                            "original_code": None,
                            "records": [],
                            "message": "Mã đổi không tồn tại"
                        }
                    
                    # Trường hợp chỉ có mã mà không có bản ghi
                    return {
                        "success": True,
                        "has_warranty": redemption_code_obj.has_warranty,
                        "warranty_valid": True if not redemption_code_obj.warranty_expires_at or redemption_code_obj.warranty_expires_at > get_now() else False,
                        "warranty_expires_at": redemption_code_obj.warranty_expires_at.isoformat() if redemption_code_obj.warranty_expires_at else None,
                        "banned_teams": [],
                        "can_reuse": False,
                        "original_code": redemption_code_obj.code,
                        "records": [{
                            "code": redemption_code_obj.code,
                            "has_warranty": redemption_code_obj.has_warranty,
                            "warranty_valid": True if not redemption_code_obj.warranty_expires_at or redemption_code_obj.warranty_expires_at > get_now() else False,
                            "status": redemption_code_obj.status,
                            "used_at": None,
                            "team_id": None,
                            "team_name": None,
                            "team_status": None,
                            "team_expires_at": None,
                            "warranty_expires_at": redemption_code_obj.warranty_expires_at.isoformat() if redemption_code_obj.warranty_expires_at else None
                        }],
                        "message": "Mã đổi chưa được sử dụng"
                    }

            elif email:
                # Tìm tất cả bản ghi đổi thông qua email
                stmt = (
                    select(RedemptionRecord, RedemptionCode, Team)
                    .options(selectinload(RedemptionRecord.redemption_code), selectinload(RedemptionRecord.team))
                    .join(RedemptionCode, RedemptionRecord.code == RedemptionCode.code)
                    .join(Team, RedemptionRecord.team_id == Team.id)
                    .where(RedemptionRecord.email == email)
                    .order_by(RedemptionRecord.redeemed_at.desc())
                )
                result = await db_session.execute(stmt)
                all_records = result.all()

                # Chỉ giữ lại bản ghi gần nhất cho mỗi mã đổi
                seen_codes = set()
                records_data = []
                for row in all_records:
                    # Định dạng dòng: (RedemptionRecord, RedemptionCode, Team)
                    record_obj = row[0]
                    if record_obj.code not in seen_codes:
                        seen_codes.add(record_obj.code)
                        records_data.append(row)

            if not records_data:
                return {
                    "success": True,
                    "has_warranty": False,
                    "warranty_valid": False,
                    "warranty_expires_at": None,
                    "banned_teams": [],
                    "can_reuse": False,
                    "original_code": None,
                    "records": [],
                    "message": "Không tìm thấy bản ghi đổi"
                }

            # 2. Xử lý bản ghi và thực hiện đồng bộ thời gian thực cần thiết
            final_records = []
            banned_teams_info = []
            has_any_warranty = False
            primary_warranty_valid = False
            primary_expiry = None
            primary_code = None
            can_reuse = False

            for record, code_obj, team in records_data:
                # 1.1 实时一致性校验 (自愈逻辑)
                # 如果数据库有记录，但 API 列表里没你，说明是虚假成功，直接后台修复
                if team.status != "banned" and team.status != "expired":
                    logger.info(f"质保查询: 正在实时测试 Team {team.id} ({team.team_name}) 的状态")
                    sync_res = await self.team_service.sync_team_info(team.id, db_session)
                    member_emails = [m.lower() for m in sync_res.get("member_emails", [])]
                    
                    if record.email.lower() not in member_emails:
                        logger.warning(f"自愈逻辑(查询触发): 发现孤儿记录 (Email: {record.email}, Team: {team.id}), API 查无此人。正在执行自动清理。")
                        await db_session.delete(record)
                        await db_session.commit()
                        # 跳过这条无效记录，提示用户重新兑换
                        continue 

                # Tính toán/trích xuất thông tin bảo hành một cách động
                expiry_date = code_obj.warranty_expires_at
                
                # Nếu là mã bảo hành và đã sử dụng nhưng không có thời gian hết hạn, thử tính toán động
                if code_obj.has_warranty and not expiry_date:
                    start_time = code_obj.used_at or record.redeemed_at # 优先取首次使用时间
                    if start_time:
                        days = code_obj.warranty_days or 30
                        expiry_date = start_time + timedelta(days=days)

                is_valid = True
                if expiry_date and expiry_date < get_now():
                    is_valid = False
                elif not expiry_date and code_obj.has_warranty and code_obj.status == "unused":
                    # Mã bảo hành chưa sử dụng, tạm thời đánh dấu là còn hiệu lực
                    is_valid = True
                elif not expiry_date:
                    # Không có ngày cũng không có bản ghi, thường là mã không có bảo hành
                    is_valid = False

                if code_obj.has_warranty:
                    has_any_warranty = True
                    # Lấy mã bảo hành gần nhất làm tham chiếu trạng thái bảo hành chính
                    if primary_code is None:
                        primary_warranty_valid = is_valid
                        primary_expiry = expiry_date
                        primary_code = code_obj.code

                # Ghi nhận các Team bị khóa (banned)
                if team.status == "banned":
                    banned_teams_info.append({
                        "team_id": team.id,
                        "team_name": team.team_name,
                        "email": team.email,
                        "banned_at": team.last_sync.isoformat() if team.last_sync else None
                    })

                final_records.append({
                    "code": code_obj.code,
                    "has_warranty": code_obj.has_warranty,
                    "warranty_valid": is_valid,
                    "warranty_expires_at": expiry_date.isoformat() if expiry_date else None,
                    "status": code_obj.status,
                    "used_at": record.redeemed_at.isoformat() if record.redeemed_at else None,
                    "team_id": team.id,
                    "team_name": team.team_name,
                    "team_status": team.status,
                    "team_expires_at": team.expires_at.isoformat() if team.expires_at else None,
                    "email": record.email,
                    "device_code_auth_enabled": team.device_code_auth_enabled
                })

            # 3. Xác định có thể sử dụng lại hay không (chỉ cần có mã bảo hành hợp lệ và có Team bị khóa)
            if has_any_warranty and primary_warranty_valid and len(banned_teams_info) > 0:
                # Xác minh thêm (tái sử dụng logic validate_warranty_reuse hiện có)
                # Ở đây để đơn giản thì tái sử dụng trực tiếp logic có sẵn
                can_reuse = True

            # 4. Xác định trạng thái cuối cùng
            message = "Tra cứu thành công"
            if has_any_warranty and not final_records and records_data:
                # Trường hợp này cho thấy tất cả bản ghi vừa rồi đều bị cơ chế tự chữa (tự động sửa) xóa bỏ (tất cả đều là thành công ảo)
                message = "Hệ thống phát hiện bản ghi đổi của bạn có vấn đề đồng bộ và đã tự động sửa! Mã đổi của bạn đã được khôi phục, vui lòng quay lại trang đổi mã và gửi lại một lần nữa."
                can_reuse = True

            return {
                "success": True,
                "has_warranty": has_any_warranty,
                "warranty_valid": primary_warranty_valid,
                "warranty_expires_at": primary_expiry.isoformat() if primary_expiry else None,
                "banned_teams": banned_teams_info,
                "can_reuse": can_reuse,
                "original_code": primary_code,
                "records": final_records,
                "message": message
            }

        except Exception as e:
            logger.error(f"Kiểm tra trạng thái bảo hành thất bại: {e}")
            return {
                "success": False,
            "error": f"Kiểm tra trạng thái bảo hành thất bại: {str(e)}"
            }

    async def validate_warranty_reuse(
        self,
        db_session: AsyncSession,
        code: str,
        email: str
    ) -> Dict[str, Any]:
        """
        Xác minh xem mã bảo hành có thể sử dụng lại hay không

        Args:
            db_session: Phiên làm việc với cơ sở dữ liệu
            code: Mã đổi
            email: Email người dùng

        Returns:
            Từ điển kết quả, bao gồm success, can_reuse, reason, error
        """
        try:
            # 1. Truy vấn mã đổi
            stmt = select(RedemptionCode).where(RedemptionCode.code == code)
            result = await db_session.execute(stmt)
            redemption_code = result.scalar_one_or_none()

            if not redemption_code:
                return {
                    "success": True,
                    "can_reuse": False,
                    "reason": "Mã đổi không tồn tại",
                    "error": None
                }

            # 2. Kiểm tra có phải mã bảo hành hay không
            if not redemption_code.has_warranty:
                return {
                    "success": True,
                    "can_reuse": False,
                    "reason": "Mã đổi này không phải là mã bảo hành",
                    "error": None
                }

            # 3. Kiểm tra thời hạn bảo hành có còn hiệu lực hay không
            if redemption_code.warranty_expires_at:
                if redemption_code.warranty_expires_at < get_now():
                    return {
                        "success": True,
                        "can_reuse": False,
                    "reason": "Bảo hành đã hết hạn",
                        "error": None
                    }

            # 4. Kiểm tra hiện tại mã đổi này có Team đang sử dụng nào còn hoạt động hay không (kiểm tra toàn cục, không giới hạn email)
            # Logic: Nếu dưới mã này có bất kỳ Team nào vẫn ở trạng thái active/full và chưa hết hạn thì không cho phép kích hoạt mới
            stmt = select(RedemptionRecord).where(RedemptionRecord.code == code)
            result = await db_session.execute(stmt)
            all_records_for_code = result.scalars().all()
            
            for record in all_records_for_code:
                stmt = select(Team).where(Team.id == record.team_id)
                result = await db_session.execute(stmt)
                team = result.scalar_one_or_none()
                
                if team:
                    is_expired = team.expires_at and team.expires_at < get_now()
                    if team.status in ["active", "full"] and not is_expired:
                        # --- Logic tự chữa: xác minh xem có thực sự ở trong Team hay không ---
                        # Dùng để dọn các bản ghi kéo người còn sót lại do "thành công ảo"
                        logger.info(f"Xác minh dùng lại bảo hành: phát hiện bản ghi đang hoạt động, đang đồng bộ Team {team.id} để kiểm tra thành viên có tồn tại hay không")
                        sync_res = await self.team_service.sync_team_info(team.id, db_session)
                        member_emails = [m.lower() for m in sync_res.get("member_emails", [])]
                        
                        if record.email.lower() not in member_emails:
                            logger.warning(f"Logic tự chữa: phát hiện bản ghi mồ côi (Email: {record.email}, Team: {team.id}), nhưng kết quả đồng bộ không chứa thành viên này. Đang xóa bản ghi.")
                            # Xóa bản ghi mồ côi
                            await db_session.delete(record)
                            if not db_session.in_transaction():
                                await db_session.commit()
                            else:
                                await db_session.flush()
                            continue # Tiếp tục kiểm tra bản ghi tiếp theo hoặc kết thúc vòng lặp

                        # Nếu cùng một email và thực sự đang trong Team, thông báo là đã ở trong Team hợp lệ
                        if record.email == email:
                            return {
                                "success": True,
                                "can_reuse": False,
                                "reason": f"Bạn đã ở trong Team hợp lệ ({team.team_name or team.id}), không thể đổi lại",
                                "error": None
                            }
                        else:
                            # Nếu là email khác, thông báo mã đã bị chiếm dụng
                            return {
                                "success": True,
                                "can_reuse": False,
                                "reason": "Mã đổi này hiện đang được tài khoản khác sử dụng. Nếu muốn đổi lại, hãy đảm bảo tài khoản cũ đã rời Team hoặc Team cũ đã không còn hiệu lực.",
                                "error": None
                            }

            # Làm mới danh sách bản ghi (có thể ở bước trên đã xóa các bản ghi mồ côi bởi logic tự chữa)
            stmt = select(RedemptionRecord).where(RedemptionRecord.code == code)
            result = await db_session.execute(stmt)
            all_records_for_code = result.scalars().all()

            # 5. Tìm bản ghi sử dụng mã đổi này của người dùng hiện tại (phục vụ phán đoán logic tiếp theo)
            records = [r for r in all_records_for_code if r.email == email]
            
            if not records:
                # Trước đó không có bản ghi nào với email này, nhưng phía trên đã kiểm tra không có Team hoạt động nào khác, nên cho phép “mở mới” hoặc “tiếp nhận”
                return {
                    "success": True,
                    "can_reuse": True,
                    "reason": "Có thể đổi tên để sử dụng (hoặc là lần sử dụng đầu tiên)",
                    "error": None
                }

            # 5. Kiểm tra hiện tại người dùng có đang ở trong Team hợp lệ nào không
            # Logic: Nếu Team tham gia gần nhất vẫn còn hiệu lực (active/full và chưa hết hạn) thì không cho phép dùng lại
            for record in records:
                stmt = select(Team).where(Team.id == record.team_id)
                result = await db_session.execute(stmt)
                team = result.scalar_one_or_none()
                
                if team:
                    # Nếu có bất kỳ Team liên quan nào vẫn ở trạng thái active/full và chưa hết hạn
                    is_expired = team.expires_at and team.expires_at < get_now()
                    if team.status in ["active", "full"] and not is_expired:
                        return {
                            "success": True,
                            "can_reuse": False,
                                "reason": f"Bạn đã ở trong Team hợp lệ ({team.team_name or team.id}), không thể đổi lại",
                            "error": None
                        }

            # 6. Kiểm tra có bản ghi nào bị khóa (banned) hay không
            has_banned_team = False
            for record in records:
                stmt = select(Team).where(Team.id == record.team_id)
                result = await db_session.execute(stmt)
                team = result.scalar_one_or_none()
                if team and team.status == "banned":
                    has_banned_team = True
                    break
            if has_banned_team:
                return {
                    "success": True,
                    "can_reuse": True,
                    "reason": "Team trước đó bạn tham gia đã bị khóa, có thể dùng bảo hành để đổi lại",
                    "error": None
                }
            else:
                return {
                    "success": True,
                    "can_reuse": False,
                    "reason": "Không tìm thấy bản ghi bị khóa, và bảo hành không hỗ trợ đổi lại trong trường hợp hết hạn bình thường hoặc lỗi khác",
                    "error": None
                }

        except Exception as e:
            logger.error(f"Xác minh dùng lại mã bảo hành thất bại: {e}")
            return {
                "success": False,
                "can_reuse": False,
                "reason": None,
                "error": f"Xác minh thất bại: {str(e)}"
            }


# Tạo instance dịch vụ bảo hành toàn cục
warranty_service = WarrantyService()
