/**
 * Hệ thống Quản lý GPT Team - JavaScript Chung
 */

// Hàm hiển thị thông báo Toast
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

// Hàm định dạng ngày giờ
function formatDateTime(dateString) {
    if (!dateString) return '-';

    const date = new Date(dateString);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// Hàm đăng xuất
async function logout() {
    if (!confirm('Bạn có chắc muốn đăng xuất không?')) {
        return;
    }

    try {
        const response = await fetch('/auth/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            window.location.href = '/login';
        } else {
            showToast('Đăng xuất thất bại', 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối', 'error');
    }
}

// Hàm gọi API
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || data.detail || 'Yêu cầu thất bại');
        }

        return { success: true, data };
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Hộp thoại xác nhận
function confirmAction(message) {
    return confirm(message);
}

// Thực hiện sau khi trang tải xong
document.addEventListener('DOMContentLoaded', function () {
    // Kiểm tra trạng thái xác thực
    checkAuthStatus();
});

// Kiểm tra trạng thái xác thực
async function checkAuthStatus() {
    // Bỏ qua kiểm tra nếu đang ở trang đăng nhập
    if (window.location.pathname === '/login') {
        return;
    }

    try {
        const response = await fetch('/auth/status');
        const data = await response.json();

        if (!data.authenticated && window.location.pathname.startsWith('/admin')) {
            // Chưa đăng nhập và đang ở trang admin, chuyển đến trang đăng nhập
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Kiểm tra trạng thái xác thực thất bại:', error);
    }
}

// === Điều khiển Modal ===

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden'; // Ngăn cuộn nền
    }
}

function hideModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('show');
        document.body.style.overflow = '';
    }
}

function switchModalTab(modalId, tabId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    // Chuyển đổi trạng thái tab
    const tabs = modal.querySelectorAll('.modal-tab-btn');
    tabs.forEach(tab => {
        if (tab.getAttribute('onclick').includes(`'${tabId}'`)) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Chuyển đổi hiển thị panel
    const panels = modal.querySelectorAll('.import-panel, .card-body');
    panels.forEach(panel => {
        if (panel.id === tabId) {
            panel.style.display = 'block';
        } else {
            panel.style.display = 'none';
        }
    });
}

/**
 * Hiển thị/ẩn ô nhập thời hạn bảo hành
 */
function toggleWarrantyDays(checkbox, targetId) {
    const target = document.getElementById(targetId);
    if (target) {
        target.style.display = checkbox.checked ? 'block' : 'none';
    }
}

// === Logic Nhập Team ===

async function handleSingleImport(event) {
    event.preventDefault();
    const form = event.target;
    const accessToken = form.accessToken.value.trim();
    const refreshToken = form.refreshToken ? form.refreshToken.value.trim() : null;
    const sessionToken = form.sessionToken ? form.sessionToken.value.trim() : null;
    const clientId = form.clientId ? form.clientId.value.trim() : null;
    const email = form.email.value.trim();
    const accountId = form.accountId.value.trim();
    const submitButton = form.querySelector('button[type="submit"]');

    submitButton.disabled = true;
    submitButton.textContent = 'Đang nhập...';

    try {
        const result = await apiCall('/admin/teams/import', {
            method: 'POST',
            body: JSON.stringify({
                import_type: 'single',
                access_token: accessToken,
                refresh_token: refreshToken || null,
                session_token: sessionToken || null,
                client_id: clientId || null,
                email: email || null,
                account_id: accountId || null
            })
        });

        if (result.success) {
            showToast('Nhập Team thành công!', 'success');
            form.reset();
            setTimeout(() => location.reload(), 1500);
        } else {
            showToast(result.error || 'Nhập thất bại', 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối', 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Nhập';
    }
}

async function handleBatchImport(event) {
    event.preventDefault();
    const form = event.target;
    const batchContent = form.batchContent.value.trim();
    const submitButton = form.querySelector('button[type="submit"]');

    // Các phần tử UI
    const progressContainer = document.getElementById('batchProgressContainer');
    const progressBar = document.getElementById('batchProgressBar');
    const progressStage = document.getElementById('batchProgressStage');
    const progressPercent = document.getElementById('batchProgressPercent');
    const successCountEl = document.getElementById('batchSuccessCount');
    const failedCountEl = document.getElementById('batchFailedCount');
    const resultsContainer = document.getElementById('batchResultsContainer');
    const resultsDiv = document.getElementById('batchResults');
    const finalSummaryEl = document.getElementById('batchFinalSummary');

    // Đặt lại UI
    progressContainer.style.display = 'block';
    resultsContainer.style.display = 'none';
    progressBar.style.width = '0%';
    progressStage.textContent = 'Đang chuẩn bị nhập...';
    progressPercent.textContent = '0%';
    successCountEl.textContent = '0';
    failedCountEl.textContent = '0';
    resultsDiv.innerHTML = '<table class="data-table"><thead><tr><th>Email</th><th>Trạng thái</th><th>Thông báo</th></tr></thead><tbody id="batchResultsBody"></tbody></table>';
    const resultsBody = document.getElementById('batchResultsBody');

    submitButton.disabled = true;
    submitButton.textContent = 'Đang nhập...';

    try {
        const response = await fetch('/admin/teams/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                import_type: 'batch',
                content: batchContent
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || errorData.detail || 'Yêu cầu thất bại');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Dòng cuối có thể chưa hoàn chỉnh

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);

                    if (data.type === 'start') {
                        progressStage.textContent = `Bắt đầu nhập (Tổng ${data.total} mục)...`;
                    } else if (data.type === 'progress') {
                        const percent = Math.round((data.current / data.total) * 100);
                        progressBar.style.width = `${percent}%`;
                        progressPercent.textContent = `${percent}%`;
                        progressStage.textContent = `Đang nhập ${data.current}/${data.total}...`;
                        successCountEl.textContent = data.success_count;
                        failedCountEl.textContent = data.failed_count;

                        // Thêm kết quả thời gian thực vào danh sách chi tiết
                        if (data.last_result) {
                            resultsContainer.style.display = 'block';
                            const res = data.last_result;
                            const statusClass = res.success ? 'text-success' : 'text-danger';
                            const statusText = res.success ? 'Thành công' : 'Thất bại';
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td>${res.email}</td>
                                <td class="${statusClass}">${statusText}</td>
                                <td>${res.success ? (res.message || 'Nhập thành công') : res.error}</td>
                            `;
                            // Thêm vào đầu danh sách để xem kết quả mới nhất
                            resultsBody.insertBefore(row, resultsBody.firstChild);
                        }
                    } else if (data.type === 'finish') {
                        progressStage.textContent = 'Nhập hoàn tất';
                        progressBar.style.width = '100%';
                        progressPercent.textContent = '100%';
                        finalSummaryEl.textContent = `Tổng: ${data.total} | Thành công: ${data.success_count} | Thất bại: ${data.failed_count}`;

                        if (data.failed_count === 0) {
                            showToast('Nhập toàn bộ thành công!', 'success');
                        } else {
                            showToast(`Nhập hoàn tất, thành công ${data.success_count}, thất bại ${data.failed_count}`, 'warning');
                        }

                        // Tải lại trang để hiển thị dữ liệu mới
                        if (data.success_count > 0) {
                            setTimeout(() => location.reload(), 3000);
                        }
                    } else if (data.type === 'error') {
                        showToast(data.error, 'error');
                    }
                } catch (e) {
                    console.error('Lỗi phân tích dữ liệu stream:', e, line);
                }
            }
        }
    } catch (error) {
        showToast(error.message || 'Lỗi kết nối', 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = 'Nhập hàng loạt';
    }
}

// === Logic Tạo Mã đổi ===

async function generateSingle(event) {
    event.preventDefault();
    const form = event.target;
    const customCode = form.customCode.value.trim();
    const expiresDays = form.expiresDays.value;
    const hasWarranty = form.hasWarranty.checked;
    const warrantyDays = form.warrantyDays ? form.warrantyDays.value : 30;

    const data = {
        type: 'single',
        has_warranty: hasWarranty,
        warranty_days: parseInt(warrantyDays || 30)
    };
    if (customCode) data.code = customCode;
    if (expiresDays) data.expires_days = parseInt(expiresDays);

    const result = await apiCall('/admin/codes/generate', {
        method: 'POST',
        body: JSON.stringify(data)
    });

    if (result.success) {
        document.getElementById('generatedCode').textContent = result.data.code;
        document.getElementById('singleResult').style.display = 'block';
        form.reset();
        showToast('Tạo mã đổi thành công', 'success');
        // Nếu đang ở trang danh sách, làm mới sau khi tạo
        if (window.location.pathname === '/admin/codes') {
            setTimeout(() => location.reload(), 2000);
        }
    } else {
        showToast(result.error || 'Tạo thất bại', 'error');
    }
}

async function generateBatch(event) {
    event.preventDefault();
    const form = event.target;
    const count = parseInt(form.count.value);
    const expiresDays = form.expiresDays.value;
    const hasWarranty = form.hasWarranty.checked;
    const warrantyDays = form.warrantyDays ? form.warrantyDays.value : 30;

    if (count < 1 || count > 1000) {
        showToast('Số lượng tạo phải từ 1 đến 1000', 'error');
        return;
    }

    const data = {
        type: 'batch',
        count: count,
        has_warranty: hasWarranty,
        warranty_days: parseInt(warrantyDays || 30)
    };
    if (expiresDays) data.expires_days = parseInt(expiresDays);

    const result = await apiCall('/admin/codes/generate', {
        method: 'POST',
        body: JSON.stringify(data)
    });

    if (result.success) {
        document.getElementById('batchTotal').textContent = result.data.total;
        document.getElementById('batchCodes').value = result.data.codes.join('\n');
        document.getElementById('batchResult').style.display = 'block';
        form.reset();
        showToast(`Tạo thành công ${result.data.total} mã đổi`, 'success');
        if (window.location.pathname === '/admin/codes') {
            setTimeout(() => location.reload(), 3000);
        }
    } else {
        showToast(result.error || 'Tạo thất bại', 'error');
    }
}

// Hàm sao chép vào clipboard
async function copyToClipboard(text) {
    if (!text) return;

    try {
        // Thử dùng Modern Clipboard API
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
            showToast('Đã sao chép vào clipboard', 'success');
            return true;
        }
    } catch (err) {
        console.error('Sao chép thất bại (API mới):', err);
    }

    // Fallback: dùng phương thức textarea
    try {
        const textArea = document.createElement("textarea");
        textArea.value = text;

        // Đảm bảo textarea không hiển thị và không ảnh hưởng layout
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "0";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);

        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (successful) {
            showToast('Đã sao chép vào clipboard', 'success');
            return true;
        }
    } catch (err) {
        console.error('Sao chép thất bại (phương thức dự phòng):', err);
    }

    showToast('Sao chép thất bại', 'error');
    return false;
}

// === Hàm hỗ trợ ===

function copyCode(code) {
    // Nếu không truyền code, lấy từ kết quả đã tạo
    if (!code) {
        const generatedCodeEl = document.getElementById('generatedCode');
        code = generatedCodeEl ? generatedCodeEl.textContent : '';
    }

    if (code) {
        copyToClipboard(code);
    } else {
        showToast('Không có nội dung để sao chép', 'error');
    }
}

function copyBatchCodes() {
    const codes = document.getElementById('batchCodes').value;
    copyToClipboard(codes);
}

function downloadCodes() {
    const codes = document.getElementById('batchCodes').value;
    const blob = new Blob([codes], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ma_doi_${new Date().getTime()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Tải xuống thành công', 'success');
}

// === Logic Quản lý Thành viên ===

async function syncTeamMemberCount(teamId) {
    // Đồng bộ số thành viên hiển thị trên Dashboard (bảng Team) sau khi thao tác trong modal
    try {
        const info = await apiCall(`/admin/teams/${teamId}/info`);
        if (!info.success) return;

        const team = info.data.team;
        if (!team) return;

        // Cập nhật cột "Thành viên" trong bảng Dashboard nếu có
        const viewBtn = document.querySelector(`.btn-view-members[data-id="${teamId}"]`);
        const row = viewBtn ? viewBtn.closest('tr') : null;
        const memberCountEl = row ? row.querySelector('.member-count') : null;
        if (memberCountEl) {
            memberCountEl.textContent = `${team.current_members}/${team.max_members}`;
        }
    } catch (e) {
        // Không chặn luồng UX nếu sync thất bại
        console.warn('syncTeamMemberCount failed:', e);
    }
}

async function viewMembers(teamId, teamEmail = '') {
    window.currentTeamId = teamId;
    const modal = document.getElementById('manageMembersModal');
    if (!modal) return;

    // Thiết lập thông tin cơ bản
    document.getElementById('modalTeamEmail').textContent = teamEmail;

    // Mở modal
    showModal('manageMembersModal');

    // Tải danh sách thành viên
    await loadModalMemberList(teamId);
}

async function loadModalMemberList(teamId) {
    const joinedTableBody = document.getElementById('modalJoinedMembersTableBody');
    const invitedTableBody = document.getElementById('modalInvitedMembersTableBody');

    if (joinedTableBody) joinedTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Đang tải...</td></tr>';
    if (invitedTableBody) invitedTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">Đang tải...</td></tr>';

    try {
        const result = await apiCall(`/admin/teams/${teamId}/members/list`);
        if (result.success) {
            const allMembers = result.data.members || [];
            const joinedMembers = allMembers.filter(m => m.status === 'joined');
            const invitedMembers = allMembers.filter(m => m.status === 'invited');

            // Hiển thị thành viên đã tham gia
            if (joinedTableBody) {
                if (joinedMembers.length === 0) {
                    joinedTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 1.5rem; color: var(--text-muted);">Chưa có thành viên nào tham gia</td></tr>';
                } else {
                    joinedTableBody.innerHTML = joinedMembers.map(m => `
                        <tr>
                            <td>${m.email}</td>
                            <td>
                                <span class="role-badge role-${m.role}">
                                    ${m.role === 'account-owner' ? 'Chủ sở hữu' : 'Thành viên'}
                                </span>
                            </td>
                            <td>${formatDateTime(m.added_at)}</td>
                            <td style="text-align: right;">
                                ${m.role !== 'account-owner' ? `
                                    <button onclick="deleteMember('${teamId}', '${m.user_id}', '${m.email}', true)" class="btn btn-sm btn-danger">
                                        <i data-lucide="trash-2"></i> Xóa
                                    </button>
                                ` : '<span class="text-muted">Không thể xóa</span>'}
                            </td>
                        </tr>
                    `).join('');
                }
            }

            // Hiển thị thành viên đang chờ
            if (invitedTableBody) {
                if (invitedMembers.length === 0) {
                    invitedTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 1.5rem; color: var(--text-muted);">Chưa có thành viên nào đang chờ</td></tr>';
                } else {
                    invitedTableBody.innerHTML = invitedMembers.map(m => `
                        <tr>
                            <td>${m.email}</td>
                            <td>
                                <span class="role-badge role-${m.role}">Thành viên</span>
                            </td>
                            <td>${formatDateTime(m.added_at)}</td>
                            <td style="text-align: right;">
                                <button onclick="revokeInvite('${teamId}', '${m.email}', true)" class="btn btn-sm btn-warning">
                                    <i data-lucide="undo"></i> Thu hồi
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
            }

            if (window.lucide) lucide.createIcons();
        } else {
            const errorMsg = `<tr><td colspan="4" style="text-align: center; color: var(--danger);">${result.error}</td></tr>`;
            if (joinedTableBody) joinedTableBody.innerHTML = errorMsg;
            if (invitedTableBody) invitedTableBody.innerHTML = errorMsg;
        }
    } catch (error) {
        const errorMsg = '<tr><td colspan="4" style="text-align: center; color: var(--danger);">Tải thất bại</td></tr>';
        if (joinedTableBody) joinedTableBody.innerHTML = errorMsg;
        if (invitedTableBody) invitedTableBody.innerHTML = errorMsg;
    }
}

async function revokeInvite(teamId, email, inModal = false) {
    if (!confirm(`Bạn có chắc muốn thu hồi lời mời của "${email}" không?`)) {
        return;
    }

    try {
        showToast('Đang thu hồi...', 'info');
        const result = await apiCall(`/admin/teams/${teamId}/invites/revoke`, {
            method: 'POST',
            body: JSON.stringify({ email: email })
        });

        if (result.success) {
            showToast('Thu hồi thành công', 'success');
            if (inModal) {
                await loadModalMemberList(teamId);
                await syncTeamMemberCount(teamId);
            } else {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showToast(result.error || 'Thu hồi thất bại', 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối', 'error');
    }
}

async function handleAddMember(event) {
    event.preventDefault();
    const form = event.target;
    const email = form.email.value.trim();
    const submitButton = document.getElementById('addMemberSubmitBtn');
    const teamId = window.currentTeamId;

    if (!teamId) {
        showToast('Không thể lấy Team ID', 'error');
        return;
    }

    submitButton.disabled = true;
    const originalText = submitButton.innerHTML;
    submitButton.textContent = 'Đang thêm...';

    try {
        const result = await apiCall(`/admin/teams/${teamId}/members/add`, {
            method: 'POST',
            body: JSON.stringify({ email })
        });

        if (result.success) {
            showToast('Thêm thành viên thành công!', 'success');
            form.reset();
            // Trong modal, chỉ tải lại danh sách
            if (document.getElementById('manageMembersModal').classList.contains('show')) {
                await loadModalMemberList(teamId);
                await syncTeamMemberCount(teamId);
            } else {
                setTimeout(() => location.reload(), 1500);
            }
        } else {
            showToast(result.error || 'Thêm thất bại', 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối', 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }
}

async function deleteMember(teamId, userId, email, inModal = false) {
    if (!confirm(`Bạn có chắc muốn xóa thành viên "${email}" không?\n\nHành động này không thể hoàn tác!`)) {
        return;
    }

    try {
        showToast('Đang xóa...', 'info');
        const result = await apiCall(`/admin/teams/${teamId}/members/${userId}/delete`, {
            method: 'POST'
        });

        if (result.success) {
            showToast('Xóa thành công', 'success');
            if (inModal) {
                await loadModalMemberList(teamId);
                await syncTeamMemberCount(teamId);
            } else {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showToast(result.error || 'Xóa thất bại', 'error');
        }
    } catch (error) {
        showToast('Lỗi kết nối', 'error');
    }
}
