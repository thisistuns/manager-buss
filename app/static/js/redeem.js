// JavaScript Trang Đổi Mã Người Dùng

// Hàm chuyển đổi HTML - Phòng chống XSS
function escapeHtml(unsafe) {
    if (unsafe === null || unsafe === undefined) {
        return '';
    }
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Biến toàn cục
let currentEmail = '';
let currentCode = '';
let availableTeams = [];
let selectedTeamId = null;

// Hàm thông báo Toast
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    let icon = 'info';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'alert-circle';

    toast.innerHTML = `<i data-lucide="${icon}"></i><span>${message}</span>`;
    toast.className = `toast ${type} show`;

    if (window.lucide) {
        lucide.createIcons();
    }

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Chuyển đổi bước
function showStep(stepNumber) {
    document.querySelectorAll('.step').forEach(step => {
        step.classList.remove('active');
        step.style.display = ''; // Xóa inline style, để CSS kiểm soát
    });
    const targetStep = document.getElementById(`step${stepNumber}`);
    if (targetStep) {
        targetStep.classList.add('active');
    }
}

// Quay về bước 1
function backToStep1() {
    showStep(1);
    selectedTeamId = null;
}

// Bước 1: Xác minh mã đổi và đổi ngay
document.getElementById('verifyForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value.trim();
    const code = document.getElementById('code').value.trim();
    const verifyBtn = document.getElementById('verifyBtn');

    // Kiểm tra thông tin
    if (!email || !code) {
        showToast('Vui lòng điền đầy đủ thông tin', 'error');
        return;
    }

    // Lưu vào biến toàn cục
    currentEmail = email;
    currentCode = code;

    // Vô hiệu hóa nút
    verifyBtn.disabled = true;
    verifyBtn.textContent = 'Đang đổi mã...';

    // Gọi trực tiếp API đổi mã (team_id = null là tự động chọn)
    await confirmRedeem(null);

    // Khôi phục nút (nếu confirmRedeem thất bại và hiển thị lỗi thì OK, người dùng có thể nhấn quay lại để thử lại)
    verifyBtn.disabled = false;
    verifyBtn.textContent = 'Xác minh Mã đổi';
});

// Hiển thị danh sách Team
function renderTeamsList() {
    const teamsList = document.getElementById('teamsList');
    teamsList.innerHTML = '';

    availableTeams.forEach(team => {
        const teamCard = document.createElement('div');
        teamCard.className = 'team-card';
        teamCard.onclick = () => selectTeam(team.id);

        const planBadge = team.subscription_plan === 'Plus' ? 'badge-plus' : 'badge-pro';

        teamCard.innerHTML = `
            <div class="team-name">${escapeHtml(team.team_name) || 'Team ' + team.id}</div>
            <div class="team-info">
                <div class="team-info-item">
                    <i data-lucide="users" style="width: 14px; height: 14px;"></i>
                    <span>${team.current_members}/${team.max_members} thành viên</span>
                </div>
                <div class="team-info-item">
                    <span class="team-badge ${planBadge}">${escapeHtml(team.subscription_plan) || 'Plus'}</span>
                </div>
                ${team.expires_at ? `
                <div class="team-info-item">
                    <i data-lucide="calendar" style="width: 14px; height: 14px;"></i>
                    <span>Hết hạn: ${formatDate(team.expires_at)}</span>
                </div>
                ` : ''}
            </div>
        `;

        teamsList.appendChild(teamCard);
        if (window.lucide) lucide.createIcons();
    });
}

// Chọn Team
function selectTeam(teamId) {
    selectedTeamId = teamId;

    // Cập nhật UI
    document.querySelectorAll('.team-card').forEach(card => {
        card.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');

    // Xác nhận đổi mã ngay
    confirmRedeem(teamId);
}

// Tự động chọn Team
function autoSelectTeam() {
    if (availableTeams.length === 0) {
        showToast('Không có Team nào khả dụng', 'error');
        return;
    }

    // Tự động chọn Team đầu tiên (backend sẽ sắp xếp theo thời gian hết hạn)
    confirmRedeem(null);
}

// Xác nhận đổi mã
async function confirmRedeem(teamId) {
    console.log('Bắt đầu quá trình đổi mã, teamId:', teamId);

    try {
        const response = await fetch('/redeem/confirm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: currentEmail,
                code: currentCode,
                team_id: teamId
            })
        });

        console.log('Trạng thái phản hồi:', response.status);

        let data;
        const text = await response.text();
        try {
            data = JSON.parse(text);
        } catch (e) {
            console.error('Không thể phân tích JSON phản hồi:', text);
            throw new Error('Định dạng phản hồi máy chủ bị lỗi');
        }

        if (response.ok && data.success) {
            // Đổi mã thành công
            console.log('Đổi mã thành công');
            showSuccessResult(data);
        } else {
            // Đổi mã thất bại
            console.warn('Đổi mã thất bại:', data);

            // Trích xuất thông báo lỗi an toàn
            let errorMessage = 'Đổi mã thất bại';

            if (data.detail) {
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    // Xử lý lỗi xác thực FastAPI (mảng các đối tượng)
                    errorMessage = data.detail.map(err => err.msg || JSON.stringify(err)).join('; ');
                } else {
                    errorMessage = JSON.stringify(data.detail);
                }
            } else if (data.error) {
                errorMessage = data.error;
            }

            showErrorResult(errorMessage);
        }
    } catch (error) {
        console.error('Lỗi mạng hoặc logic:', error);
        showErrorResult(error.message || 'Lỗi kết nối, vui lòng thử lại sau');
    }
}

// Hiển thị kết quả thành công
function showSuccessResult(data) {
    const resultContent = document.getElementById('resultContent');
    const teamInfo = data.team_info || {};

    resultContent.innerHTML = `
        <div class="result-success">
            <div class="result-icon"><i data-lucide="check-circle" style="width: 64px; height: 64px; color: var(--success);"></i></div>
            <div class="result-title">Đổi mã thành công!</div>
            <div class="result-message">${escapeHtml(data.message) || 'Bạn đã tham gia Team thành công'}</div>

            <div class="result-details">
                <div class="result-detail-item">
                    <span class="result-detail-label">Tên Team</span>
                    <span class="result-detail-value">${escapeHtml(teamInfo.team_name) || '-'}</span>
                </div>
                <div class="result-detail-item">
                    <span class="result-detail-label">Địa chỉ Email</span>
                    <span class="result-detail-value">${escapeHtml(currentEmail)}</span>
                </div>
                ${teamInfo.expires_at ? `
                <div class="result-detail-item">
                    <span class="result-detail-label">Ngày hết hạn</span>
                    <span class="result-detail-value">${formatDate(teamInfo.expires_at)}</span>
                </div>
                ` : ''}
            </div>

            <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 2rem; background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 8px; text-align: left;">
                <i data-lucide="mail" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 5px;"></i>
                Email lời mời đã được gửi đến hộp thư của bạn, vui lòng kiểm tra và làm theo hướng dẫn trong email để chấp nhận lời mời.
            </p>

            <div style="margin-bottom: 2rem; border-top: 1px solid var(--border-base); padding-top: 1.5rem;">
                <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 1rem;">
                    <strong>Chưa nhận được email lời mời?</strong><br>
                    Nếu sau 1-5 phút vẫn chưa nhận được email (hoặc bị chặn), hãy vào phần "Tra cứu bảo hành" để tự khắc phục.
                </p>
                <button onclick="goToWarrantyFromSuccess()" class="btn btn-secondary" style="width: 100%; border-style: dashed;">
                    <i data-lucide="shield"></i> Tra cứu bảo hành / Tự khắc phục
                </button>
            </div>

            <button onclick="location.reload()" class="btn btn-primary" style="width: 100%;">
                <i data-lucide="refresh-cw"></i> Đổi mã khác
            </button>
        </div>
    `;
    if (window.lucide) lucide.createIcons();

    showStep(3);
}

// Hiển thị kết quả thất bại
function showErrorResult(errorMessage) {
    const resultContent = document.getElementById('resultContent');

    resultContent.innerHTML = `
        <div class="result-error">
            <div class="result-icon"><i data-lucide="x-circle" style="width: 64px; height: 64px; color: var(--danger);"></i></div>
            <div class="result-title">Đổi mã thất bại</div>
            <div class="result-message">${escapeHtml(errorMessage)}</div>

            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
                <button onclick="backToStep1()" class="btn btn-secondary">
                    <i data-lucide="arrow-left"></i> Quay lại thử lại
                </button>
                <button onclick="location.reload()" class="btn btn-primary">
                    <i data-lucide="rotate-ccw"></i> Bắt đầu lại
                </button>
            </div>
        </div>
    `;
    if (window.lucide) lucide.createIcons();

    showStep(3);
}

// Định dạng ngày
function formatDate(dateString) {
    if (!dateString) return '-';

    try {
        const date = new Date(dateString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    } catch (e) {
        return dateString;
    }
}

// ========== Chức năng Tra cứu Bảo hành ==========

// Tra cứu trạng thái bảo hành
async function checkWarranty() {
    const input = document.getElementById('warrantyInput').value.trim();

    // Kiểm tra đầu vào
    if (!input) {
        showToast('Vui lòng nhập mã đổi gốc hoặc email để tra cứu', 'error');
        return;
    }

    let email = null;
    let code = null;

    // Phân biệt email hay mã đổi đơn giản
    if (input.includes('@')) {
        email = input;
    } else {
        code = input;
    }

    const checkBtn = document.getElementById('checkWarrantyBtn');
    checkBtn.disabled = true;
    checkBtn.innerHTML = '<i data-lucide="loader" class="spinning"></i> Đang tra cứu...';
    if (window.lucide) lucide.createIcons();

    try {
        const response = await fetch('/warranty/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email || null,
                code: code || null
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            showWarrantyResult(data);
        } else {
            showToast(data.error || data.detail || 'Tra cứu thất bại', 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối, vui lòng thử lại sau', 'error');
    } finally {
        checkBtn.disabled = false;
        checkBtn.innerHTML = '<i data-lucide="search"></i> Tra cứu trạng thái bảo hành';
        if (window.lucide) lucide.createIcons();
    }
}

// Hiển thị kết quả tra cứu bảo hành
function showWarrantyResult(data) {
    const warrantyContent = document.getElementById('warrantyContent');

    // Xử lý trường hợp đặc biệt: "tự động khắc phục"
    if ((!data.records || data.records.length === 0) && data.can_reuse) {
        warrantyContent.innerHTML = `
            <div class="result-info" style="text-align: center; padding: 2rem;">
                <div class="result-icon"><i data-lucide="check-circle" style="width: 56px; height: 56px; color: var(--success);"></i></div>
                <div class="result-title" style="font-size: 1.25rem; margin: 1.2rem 0; color: var(--success);">Khắc phục thành công!</div>
                <div class="result-message" style="color: var(--text-primary); background: rgba(34, 197, 94, 0.05); padding: 1.2rem; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.2); line-height: 1.6;">
                    ${escapeHtml(data.message || 'Hệ thống phát hiện lỗi và đã tự động khắc phục')}
                </div>
                
                <div style="margin-top: 2rem; text-align: left; background: rgba(255,255,255,0.03); padding: 1.2rem; border-radius: 12px; border: 1px dashed var(--border-base);">
                    <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.8rem;">Vui lòng sao chép mã đổi của bạn và quay về trang chính để thử lại:</div>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <input type="text" value="${escapeHtml(data.original_code)}" readonly 
                            style="flex: 1; padding: 0.75rem; background: rgba(0,0,0,0.2); border: 1px solid var(--border-base); border-radius: 8px; color: var(--text-primary); font-family: monospace; font-size: 1.1rem;">
                        <button onclick="copyWarrantyCode('${escapeHtml(data.original_code)}')" class="btn btn-secondary" style="white-space: nowrap;">
                            <i data-lucide="copy"></i> Sao chép
                        </button>
                    </div>
                </div>

                <div style="margin-top: 2rem;">
                    <button onclick="backToStep1()" class="btn btn-primary" style="width: 100%;">
                        <i data-lucide="arrow-left"></i> Quay lại đổi mã ngay
                    </button>
                </div>
            </div>
        `;
        if (window.lucide) lucide.createIcons();
        return;
    }

    if (!data.records || data.records.length === 0) {
        warrantyContent.innerHTML = `
            <div class="result-info" style="text-align: center; padding: 2rem;">
                <div class="result-icon"><i data-lucide="info" style="width: 48px; height: 48px; color: var(--text-muted);"></i></div>
                <div class="result-title" style="font-size: 1.2rem; margin: 1rem 0;">Không tìm thấy lịch sử đổi mã</div>
                <div class="result-message" style="color: var(--text-muted);">${escapeHtml(data.message || 'Không tìm thấy dữ liệu liên quan')}</div>
            </div>
        `;
    } else {
        // 1. Tổng quan trạng thái (nếu có mã bảo hành)
        let summaryHtml = '';
        if (data.has_warranty) {
            const warrantyStatus = data.warranty_valid ?
                '<span class="badge badge-success">✓ Bảo hành còn hiệu lực</span>' :
                '<span class="badge badge-error">✗ Bảo hành đã hết hạn</span>';

            summaryHtml = `
                <div class="warranty-summary" style="margin-bottom: 2rem; padding: 1.2rem; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid var(--border-base);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.4rem;">Trạng thái bảo hành hiện tại</div>
                            <div style="font-size: 1.1rem; font-weight: 600;">${warrantyStatus}</div>
                        </div>
                        ${data.warranty_expires_at ? `
                        <div style="text-align: right;">
                            <div style="font-size: 0.9rem; color: var(--text-muted); margin-bottom: 0.4rem;">Ngày hết hạn bảo hành</div>
                            <div style="font-size: 1rem;">${formatDate(data.warranty_expires_at)}</div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        // 2. Danh sách lịch sử đổi mã
        const recordsHtml = `
            <div class="records-section">
                <h4 style="margin: 0 0 1rem 0; font-size: 1rem; color: var(--text-primary);">Lịch sử đổi mã của tôi</h4>
                <div style="display: flex; flex-direction: column; gap: 1rem;">
                    ${data.records.map(record => {
            const typeMarker = record.has_warranty ?
                '<span class="badge badge-warranty" style="background: var(--primary); color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">Mã BH</span>' :
                '<span class="badge badge-normal" style="background: rgba(255,255,255,0.1); color: var(--text-muted); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;">Mã thường</span>';

            let teamStatusBadge = '';
            if (record.team_status === 'active') teamStatusBadge = '<span style="color: var(--success); font-size: 0.8rem;">● Đang hoạt động</span>';
            else if (record.team_status === 'full') teamStatusBadge = '<span style="color: var(--success); font-size: 0.8rem;">● Đã đầy</span>';
            else if (record.team_status === 'banned') teamStatusBadge = '<span style="color: var(--danger); font-size: 0.8rem;">● Bị khóa</span>';
            else if (record.team_status === 'error') teamStatusBadge = '<span style="color: var(--warning); font-size: 0.8rem;">● Lỗi</span>';
            else if (record.team_status === 'expired') teamStatusBadge = '<span style="color: var(--text-muted); font-size: 0.8rem;">● Hết hạn</span>';
            else teamStatusBadge = `<span style="color: var(--text-muted); font-size: 0.8rem;">● ${record.team_status || 'Không rõ'}</span>`;

            return `
                            <div class="record-card" style="padding: 1rem; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 10px;">
                                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.8rem;">
                                    <div style="font-family: monospace; font-size: 1.1rem; color: var(--text-primary);">${record.code}</div>
                                    <div>${typeMarker}</div>
                                </div>
                                <div style="display: grid; grid-template-columns: 1fr 1.2fr; gap: 1rem; font-size: 0.9rem;">
                                    <div>
                                        <div style="color: var(--text-muted); margin-bottom: 0.2rem;">Team đã tham gia</div>
                                         <div style="font-weight: 500; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                                             <span>${escapeHtml(record.team_name || 'Team không rõ')}</span>
                                             <span>${teamStatusBadge}</span>
                                             ${(record.has_warranty && record.warranty_valid && record.team_status === 'banned') ? `
                                             <button onclick="oneClickReplace('${escapeHtml(record.code)}', '${escapeHtml(record.email || currentEmail)}')" class="btn btn-xs btn-primary" style="padding: 2px 8px; font-size: 0.75rem; height: auto; min-height: 0;">
                                                 Đổi Team ngay
                                             </button>
                                             ` : ''}
                                         </div>
                                     </div>
                                     <div>
                                         <div style="color: var(--text-muted); margin-bottom: 0.2rem;">Thời gian đổi mã</div>
                                         <div>${formatDate(record.used_at)}</div>
                                     </div>
                                     <div style="grid-column: span 2;">
                                         <div style="color: var(--text-muted); margin-bottom: 0.2rem;">Team hết hạn</div>
                                         <div style="font-weight: 500;">${formatDate(record.team_expires_at)}</div>
                                     </div>
                                    ${record.has_warranty ? `
                                    <div style="grid-column: span 2;">
                                        <div style="color: var(--text-muted); margin-bottom: 0.2rem;">Bảo hành hết hạn</div>
                                        <div style="${record.warranty_valid ? 'color: var(--success);' : 'color: var(--danger);'}">
                                            ${record.warranty_expires_at ? `${formatDate(record.warranty_expires_at)} ${record.warranty_valid ? '(Còn hiệu lực)' : '(Đã hết hạn)'}` : 'Chưa bắt đầu tính (kích hoạt sau lần sử dụng đầu tiên)'}
                                        </div>
                                    </div>
                                    ` : ''}
                                     <div style="grid-column: span 2; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.8rem; margin-top: 0.2rem;">
                                         <div>
                                             <div style="color: var(--text-muted); margin-bottom: 0.2rem;">Xác thực thiết bị (Codex)</div>
                                             <div style="font-weight: 500;">
                                                 ${record.device_code_auth_enabled ? '<span style="color: var(--success);">Đã bật</span>' : '<span style="color: var(--warning);">Chưa bật</span>'}
                                             </div>
                                         </div>
                                         ${(!record.device_code_auth_enabled && record.team_status !== 'banned' && record.team_status !== 'expired') ? `
                                         <button onclick="enableUserDeviceAuth(${record.team_id}, '${escapeHtml(record.code)}', '${escapeHtml(record.email)}')" class="btn btn-xs btn-primary" style="padding: 4px 10px; font-size: 0.75rem; height: auto;">
                                             Bật ngay
                                         </button>
                                         ` : ''}
                                     </div>
                                 </div>
                             </div>
                         `;
        }).join('')}
                </div>
            </div>
        `;

        // 3. Khu vực có thể đổi lại
        const canReuseHtml = data.can_reuse ? `
            <div style="margin-top: 2rem; padding: 1.5rem; background: rgba(34, 197, 94, 0.1); border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3);">
                <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--success); margin-bottom: 0.8rem;">
                    <i data-lucide="check-circle" style="width: 20px; height: 20px;"></i> 
                    <span style="font-weight: 600;">Phát hiện Team đã hết hạn, có thể kích hoạt bảo hành</span>
                </div>
                <p style="margin: 0 0 1.2rem 0; color: var(--text-secondary); font-size: 0.95rem;">
                    Phát hiện Team bạn đang sử dụng đã hết hiệu lực. Do mã bảo hành của bạn vẫn còn trong thời hạn, bạn có thể sao chép mã đổi và đổi lại ngay.
                </p>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <input type="text" value="${escapeHtml(data.original_code)}" readonly 
                        style="flex: 1; padding: 0.75rem; background: rgba(0,0,0,0.2); border: 1px solid var(--border-base); border-radius: 8px; color: var(--text-primary); font-family: monospace; font-size: 1.1rem;">
                    <button onclick="copyWarrantyCode('${escapeHtml(data.original_code)}')" class="btn btn-secondary" style="white-space: nowrap;">
                        <i data-lucide="copy"></i> Sao chép
                    </button>
                </div>
            </div>
        ` : '';

        warrantyContent.innerHTML = `
            <div class="warranty-view">
                ${summaryHtml}
                ${recordsHtml}
                ${canReuseHtml}
                <div style="margin-top: 2rem; text-align: center;">
                    <button onclick="backToStep1()" class="btn btn-secondary" style="width: 100%;">
                        <i data-lucide="arrow-left"></i> Quay lại đổi mã
                    </button>
                </div>
            </div>
        `;
    }

    if (window.lucide) lucide.createIcons();

    // Hiển thị khu vực kết quả bảo hành
    document.querySelectorAll('.step').forEach(step => step.style.display = 'none');
    document.getElementById('warrantyResult').style.display = 'block';
}

// Sao chép mã đổi bảo hành
function copyWarrantyCode(code) {
    navigator.clipboard.writeText(code).then(() => {
        showToast('Đã sao chép mã đổi vào clipboard', 'success');
    }).catch(() => {
        showToast('Sao chép thất bại, vui lòng sao chép thủ công', 'error');
    });
}

// Đổi Team ngay (một cú nhấp)
async function oneClickReplace(code, email) {
    if (!code || !email) {
        showToast('Không thể lấy đầy đủ thông tin, vui lòng thử thủ công', 'error');
        return;
    }

    // Cập nhật biến toàn cục
    currentEmail = email;
    currentCode = code;

    // Điền vào form bước 1 (để nếu thất bại người dùng quay lại vẫn thấy)
    const emailInput = document.getElementById('email');
    const codeInput = document.getElementById('code');
    if (emailInput) emailInput.value = email;
    if (codeInput) codeInput.value = code;

    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;

    // Vô hiệu hóa tất cả nút để tránh gửi trùng lặp
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" class="spinning"></i> Đang xử lý...';
    if (window.lucide) lucide.createIcons();

    showToast('Đang tự động đổi mã cho bạn...', 'info');

    try {
        // Gọi confirmRedeem trực tiếp, truyền null để tự động chọn Team
        await confirmRedeem(null);
    } catch (e) {
        console.error(e);
        showToast('Yêu cầu đổi Team thất bại', 'error');
    } finally {
        // Nếu trang không chuyển (trường hợp thất bại), khôi phục nút
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalContent;
            if (window.lucide) lucide.createIcons();
        }
    }
}

// Người dùng bật xác thực thiết bị
async function enableUserDeviceAuth(teamId, code, email) {
    if (!confirm('Bạn có chắc muốn bật xác thực mã thiết bị trong Team này không?')) {
        return;
    }

    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i data-lucide="loader" class="spinning"></i> Đang bật...';
    if (window.lucide) lucide.createIcons();

    try {
        const response = await fetch('/warranty/enable-device-auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                team_id: teamId,
                code: code,
                email: email
            })
        });

        const data = await response.json();
        if (response.ok && data.success) {
            showToast(data.message || 'Bật thành công', 'success');
            // Làm mới trạng thái hiện tại
            checkWarranty();
        } else {
            showToast(data.error || data.detail || 'Bật thất bại', 'error');
            btn.disabled = false;
            btn.innerHTML = originalContent;
            if (window.lucide) lucide.createIcons();
        }
    } catch (error) {
        showToast('Lỗi kết nối, vui lòng thử lại sau', 'error');
        btn.disabled = false;
        btn.innerHTML = originalContent;
        if (window.lucide) lucide.createIcons();
    }
}

// Chuyển từ trang thành công sang tra cứu bảo hành
function goToWarrantyFromSuccess() {
    const warrantyInput = document.getElementById('warrantyInput');
    // Ưu tiên điền email vì tìm kiếm theo email toàn diện hơn
    warrantyInput.value = currentEmail || currentCode || '';

    // Chuyển view
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById('step1').classList.add('active');
    document.getElementById('step3').style.display = 'none';

    // Cuộn đến khu vực bảo hành
    const warrantySection = document.querySelector('.warranty-section');
    if (warrantySection) {
        warrantySection.scrollIntoView({ behavior: 'smooth' });
    }

    // Tự động kích hoạt tra cứu
    checkWarranty();
}
