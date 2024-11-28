document.addEventListener('DOMContentLoaded', function() {
    // UI Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const candidatesList = document.getElementById('candidates-list');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Load candidates on page load
    loadCandidates();

    // Handle file upload
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFileUpload);
    }

    // Handle chat
    if (chatForm) {
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message) return;

            // Add user message to chat
            addChatMessage('Bạn', message);
            chatInput.value = '';

            try {
                showLoading();
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message })
                });

                const result = await response.json();
                hideLoading();

                if (!response.ok) {
                    throw new Error(result.error || 'Không thể gửi tin nhắn');
                }

                addChatMessage('Trợ lý', result.response);
            } catch (error) {
                console.error('Chat error:', error);
                hideLoading();
                showError(error.message || 'Không thể gửi tin nhắn');
            }
        });
    }

    // Helper Functions
    async function loadCandidates() {
        try {
            showLoading();
            const response = await fetch('/api/candidates');
            if (!response.ok) {
                throw new Error('Không thể tải danh sách ứng viên');
            }
            const candidates = await response.json();
            displayCandidates(candidates);
            hideLoading();
        } catch (error) {
            console.error('Error:', error);
            hideLoading();
            showError('Không thể tải danh sách ứng viên');
        }
    }

    function displayCandidates(candidates) {
        if (!candidatesList) return;
        
        candidatesList.innerHTML = candidates.map(candidate => {
            const status = candidate.status === 'error' 
                ? `<span class="badge bg-danger" title="${candidate.error_message || 'Lỗi xử lý CV'}">Lỗi</span>`
                : candidate.status === 'processing'
                ? '<span class="badge bg-warning">Đang xử lý</span>'
                : '<span class="badge bg-success">Đã xử lý</span>';
                
            return `
                <tr class="candidate-card">
                    <td>${candidate.name || 'Chưa có'}</td>
                    <td>${candidate.email || 'Chưa có'}</td>
                    <td>${candidate.phone || 'Chưa có'}</td>
                    <td>${status}</td>
                    <td>
                        <button class="btn btn-sm btn-primary view-details" data-id="${candidate.id}">
                            <i class="bi bi-eye"></i> Xem
                        </button>
                        ${candidate.status === 'processed' ? `
                        <button class="btn btn-sm btn-success evaluate" data-id="${candidate.id}">
                            <i class="bi bi-check-circle"></i> Đánh giá
                        </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    }

    function showLoading() {
        if (loadingSpinner) {
            loadingSpinner.style.display = 'block';
        }
    }

    function hideLoading() {
        if (loadingSpinner) {
            loadingSpinner.style.display = 'none';
        }
    }

    function showSuccess(message) {
        // You can implement a toast or alert here
        alert(message);
    }

    function showError(message) {
        // You can implement a toast or alert here
        alert(message);
    }

    function addChatMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender === 'Bạn' ? 'user' : 'assistant'}`;
        messageDiv.innerHTML = `
            <strong>${sender}:</strong><br>
            ${message}
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Handle candidate details view
    document.addEventListener('click', async (e) => {
        if (e.target.closest('.view-details')) {
            const button = e.target.closest('.view-details');
            const candidateId = button.dataset.id;
            try {
                showLoading();
                const response = await fetch(`/candidates/${candidateId}`);
                if (!response.ok) {
                    throw new Error('Không thể tải thông tin ứng viên');
                }
                const candidate = await response.json();
                
                // Format skills array or string
                const skills = typeof candidate.skills === 'string' 
                    ? candidate.skills.split(',').filter(s => s.trim()).join(', ')
                    : Array.isArray(candidate.skills) 
                    ? candidate.skills.join(', ')
                    : 'Chưa có';

                // Update modal content with all available information
                document.getElementById('modal-candidate-name').textContent = candidate.name || 'Thông tin ứng viên';
                document.getElementById('modal-candidate-details').innerHTML = `
                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="mb-3">Thông tin liên hệ</h6>
                            <p><strong>Email:</strong> ${candidate.email || 'Chưa có'}</p>
                            <p><strong>Số điện thoại:</strong> ${candidate.phone || 'Chưa có'}</p>
                        </div>
                        <div class="col-md-6">
                            <h6 class="mb-3">Trạng thái</h6>
                            <p><strong>Trạng thái:</strong> ${candidate.status || 'Chưa có'}</p>
                            <p><strong>Cập nhật:</strong> ${new Date(candidate.updated_at).toLocaleString('vi-VN')}</p>
                        </div>
                    </div>
                    <hr>
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6 class="mb-3">Kỹ năng và kinh nghiệm</h6>
                            <p><strong>Kỹ năng:</strong> ${skills}</p>
                            <p><strong>Kinh nghiệm:</strong></p>
                            <pre class="text-wrap bg-light p-2 rounded">${candidate.experience || 'Chưa có'}</pre>
                        </div>
                    </div>
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6 class="mb-3">Học vấn</h6>
                            <pre class="text-wrap bg-light p-2 rounded">${candidate.education || 'Chưa có'}</pre>
                        </div>
                    </div>
                    ${candidate.resume_text ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <h6 class="mb-3">Nội dung CV</h6>
                            <pre class="text-wrap bg-light p-2 rounded" style="max-height: 300px; overflow-y: auto;">
${candidate.resume_text}</pre>
                        </div>
                    </div>
                    ` : ''}
                    ${candidate.error_message ? `
                    <div class="row mt-3">
                        <div class="col-12">
                            <div class="alert alert-danger">
                                <strong>Lỗi:</strong> ${candidate.error_message}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                `;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('candidate-modal'));
                modal.show();
                hideLoading();
            } catch (error) {
                console.error('Error:', error);
                hideLoading();
                showError('Không thể tải thông tin ứng viên');
            }
        }
    });

    // Poll for candidate status updates
    async function pollCandidateStatus(candidateId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/candidates/${candidateId}`);
                const candidate = await response.json();
                
                if (candidate.status === 'processed' || candidate.status === 'error') {
                    clearInterval(pollInterval);
                    loadCandidates();
                    
                    if (candidate.status === 'error') {
                        showError(`Lỗi xử lý CV: ${candidate.error_message || 'Không xác định'}`);
                    } else {
                        showSuccess('CV đã được xử lý thành công!');
                    }
                }
            } catch (error) {
                console.error('Polling error:', error);
                clearInterval(pollInterval);
            }
        }, 2000);
    }

    // Handle file upload
    async function handleFileUpload(event) {
        event.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showError('Vui lòng chọn file CV');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            showLoading();
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Không thể tải CV lên');
            }
            
            // Start polling for status updates
            pollCandidateStatus(data.candidate_id);
            
            showSuccess('CV đã được tải lên! Đang xử lý...');
            fileInput.value = '';
            loadCandidates();
            
        } catch (error) {
            showError(error.message || 'Không thể tải CV lên');
        } finally {
            hideLoading();
        }
    }
});
