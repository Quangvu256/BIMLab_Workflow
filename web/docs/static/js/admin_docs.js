document.addEventListener('DOMContentLoaded', function () {
    const contentTypeSelect = document.getElementById('id_content_type');
    const markdownTextarea = document.getElementById('id_content_markdown');
    const contentHtmlTextarea = document.getElementById('id_content_html');
    const uploadHtmlInput = document.getElementById('id_upload_html_file');

    // =========================================================================
    // 1. Chuyển đổi Động giữa Khối Soạn thảo Markdown và Khối Upload HTML
    // =========================================================================
    const mdFieldset = document.querySelector('.fieldset-markdown');
    const htmlFieldset = document.querySelector('.fieldset-html');

    function syncContentTypeUI() {
        if (!contentTypeSelect) return;
        const selected = contentTypeSelect.value;
        if (selected === 'MARKDOWN') {
            if (mdFieldset) mdFieldset.style.display = 'block';
            if (htmlFieldset) htmlFieldset.style.display = 'none';
        } else if (selected === 'HTML') {
            if (mdFieldset) mdFieldset.style.display = 'none';
            if (htmlFieldset) htmlFieldset.style.display = 'block';
        }
    }

    if (contentTypeSelect) {
        contentTypeSelect.addEventListener('change', syncContentTypeUI);
        syncContentTypeUI();
    }

    // =========================================================================
    // 2. Giao diện Soạn thảo Markdown & Live Preview Trực quan, Sáng sủa
    // =========================================================================
    if (markdownTextarea) {
        const parent = markdownTextarea.parentElement;

        const wrapper = document.createElement('div');
        wrapper.className = 'markdown-editor-wrapper';

        const toolbar = document.createElement('div');
        toolbar.className = 'markdown-toolbar';
        toolbar.innerHTML = `
            <div class="markdown-toolbar-group">
                <button type="button" class="markdown-toolbar-btn" data-insert="## "><b>H2</b></button>
                <button type="button" class="markdown-toolbar-btn" data-insert="### "><b>H3</b></button>
                <button type="button" class="markdown-toolbar-btn" data-insert="**In đậm**"><b>B</b></button>
                <button type="button" class="markdown-toolbar-btn" data-insert="*In nghiêng*"><i>I</i></button>
            </div>
            <div class="markdown-toolbar-group">
                <button type="button" class="markdown-toolbar-btn" data-insert="| Nhóm Cấu Kiện | Danh Mục Revit | Yêu Cầu LOD 350 |\n|---|---|---|\n| Vách tường | Walls | Tách lớp hoàn thiện và xây thô |\n| Cửa đi | Doors | Khung bao, nẹp chỉ, hướng mở |\n">📊 Bảng dữ liệu</button>
                <button type="button" class="markdown-toolbar-btn" data-insert="> [!NOTE]\n> Lưu ý kỹ thuật...\n">💡 Lưu ý (Note)</button>
                <button type="button" class="markdown-toolbar-btn" data-insert="> [!WARNING]\n> Cảnh báo rủi ro...\n">⚠️ Cảnh báo</button>
                <button type="button" class="markdown-toolbar-btn" data-insert="\`\`\`mermaid\nflowchart TD\n    A([Nhận Master Coordinates]) --> B[Liên kết CAD/RVT]\n    B --> C[Dựng hình LOD 350]\n    C --> D([Nghiệm thu])\n\`\`\`\n">🔀 Sơ đồ Mermaid</button>
            </div>
            <div class="markdown-toolbar-group">
                <button type="button" class="markdown-toolbar-btn active" id="btn-mode-split" title="Chia đôi màn hình">🖥️ Chia đôi</button>
                <button type="button" class="markdown-toolbar-btn" id="btn-mode-edit" title="Chỉ soạn thảo">✏️ Soạn thảo</button>
                <button type="button" class="markdown-toolbar-btn" id="btn-mode-preview" title="Chỉ xem trước">👁️ Xem trước</button>
            </div>
            <div class="markdown-upload-badge" id="s3-status-box">
                📸 Hỗ trợ <b>Ctrl+V</b> dán ảnh lên SeaweedFS S3
            </div>
        `;

        const splitContainer = document.createElement('div');
        splitContainer.className = 'markdown-split-container';

        const leftPane = document.createElement('div');
        leftPane.className = 'markdown-pane';

        const rightPane = document.createElement('div');
        rightPane.className = 'markdown-preview-pane';
        rightPane.innerHTML = `
            <div class="markdown-preview-header">
                <span>👁️ XEM TRƯỚC THỜI GIAN THỰC (LIVE PREVIEW)</span>
                <span style="font-size:10px; color:#94a3b8; font-weight:normal;">Tự động cập nhật theo nội dung</span>
            </div>
            <div id="markdown-rendered-view" class="preview-prose"></div>
        `;

        parent.insertBefore(wrapper, markdownTextarea);
        wrapper.appendChild(toolbar);
        wrapper.appendChild(splitContainer);
        splitContainer.appendChild(leftPane);
        splitContainer.appendChild(rightPane);
        leftPane.appendChild(markdownTextarea);

        const renderedView = document.getElementById('markdown-rendered-view');
        const statusBox = document.getElementById('s3-status-box');

        // Hàm cập nhật Live Preview
        function updatePreview() {
            if (typeof marked !== 'undefined' && renderedView) {
                let val = markdownTextarea.value || '';
                // Chuyển đổi định dạng callout mềm
                val = val.replace(/> \[!(NOTE|TIP|IMPORTANT)\]\s*\n([\s\S]*?)(?=\n\n|$)/g, '> 💡 **Lưu ý:** $2');
                val = val.replace(/> \[!(WARNING|CAUTION)\]\s*\n([\s\S]*?)(?=\n\n|$)/g, '> ⚠️ **Cảnh báo:** $2');
                renderedView.innerHTML = marked.parse(val);
            }
        }

        markdownTextarea.addEventListener('input', updatePreview);
        updatePreview();

        // Chuyển đổi chế độ hiển thị (Chia đôi / Chỉ soạn / Chỉ xem trước)
        const btnSplit = document.getElementById('btn-mode-split');
        const btnEdit = document.getElementById('btn-mode-edit');
        const btnPreview = document.getElementById('btn-mode-preview');

        function setActiveModeBtn(btn) {
            [btnSplit, btnEdit, btnPreview].forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }

        btnSplit.addEventListener('click', function () {
            leftPane.style.display = 'flex';
            rightPane.style.display = 'block';
            setActiveModeBtn(btnSplit);
        });

        btnEdit.addEventListener('click', function () {
            leftPane.style.display = 'flex';
            rightPane.style.display = 'none';
            setActiveModeBtn(btnEdit);
        });

        btnPreview.addEventListener('click', function () {
            leftPane.style.display = 'none';
            rightPane.style.display = 'block';
            updatePreview();
            setActiveModeBtn(btnPreview);
        });

        // Chèn mẫu cú pháp Markdown từ thanh công cụ
        toolbar.querySelectorAll('button[data-insert]').forEach(btn => {
            btn.addEventListener('click', function () {
                insertText(markdownTextarea, this.getAttribute('data-insert'));
                updatePreview();
            });
        });

        function insertText(textarea, text) {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            textarea.value = textarea.value.substring(0, start) + text + textarea.value.substring(end);
            textarea.selectionStart = textarea.selectionEnd = start + text.length;
            textarea.focus();
        }

        // Bắt sự kiện Paste Ảnh trực tiếp (Ctrl+V) -> Tải lên SeaweedFS S3
        markdownTextarea.addEventListener('paste', function (e) {
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
            for (let i = 0; i < items.length; i++) {
                if (items[i].type.indexOf('image') !== -1) {
                    e.preventDefault();
                    const blob = items[i].getAsFile();
                    const placeholder = `\n![Đang tải ảnh lên SeaweedFS S3...]()...\n`;
                    insertText(markdownTextarea, placeholder);

                    statusBox.innerHTML = `⏳ Đang tải ảnh lên SeaweedFS S3...`;
                    statusBox.style.color = '#0284c7';

                    const formData = new FormData();
                    formData.append('image', blob);

                    fetch('/api/upload-image/', {
                        method: 'POST',
                        body: formData
                    })
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.url) {
                            const mdImage = `\n![${data.filename}](${data.url})\n`;
                            markdownTextarea.value = markdownTextarea.value.replace(placeholder, mdImage);
                            statusBox.innerHTML = `✅ Đã lưu ảnh thành công: ${data.filename}`;
                            statusBox.style.color = '#16a34a';
                            setTimeout(() => {
                                statusBox.innerHTML = `📸 Hỗ trợ <b>Ctrl+V</b> dán ảnh lên SeaweedFS S3`;
                                statusBox.style.color = '#64748b';
                            }, 4000);
                            updatePreview();
                        } else {
                            alert('Lỗi tải ảnh: ' + (data.error || 'Upload thất bại'));
                            markdownTextarea.value = markdownTextarea.value.replace(placeholder, '');
                            statusBox.innerHTML = `❌ Lỗi tải ảnh`;
                            statusBox.style.color = '#dc2626';
                        }
                    })
                    .catch(err => {
                        alert('Lỗi kết nối S3: ' + err.message);
                        markdownTextarea.value = markdownTextarea.value.replace(placeholder, '');
                    });
                    break;
                }
            }
        });
    }

    // =========================================================================
    // 3. Khối Upload Tệp HTML Độc lập: Nạp Trực tiếp Vào CSDL PostgreSQL
    // =========================================================================
    if (contentHtmlTextarea) {
        const htmlRow = contentHtmlTextarea.closest('.form-row') || contentHtmlTextarea.parentElement;
        const uploadRow = uploadHtmlInput ? (uploadHtmlInput.closest('.form-row') || uploadHtmlInput.parentElement) : null;

        const card = document.createElement('div');
        card.className = 'html-upload-card';
        card.innerHTML = `
            <div style="margin-bottom: 12px;">
                <div style="font-weight: 700; font-size: 13.5px; color: #0f172a; margin-bottom: 4px;">
                    📂 Tải lên Tệp HTML Độc lập (Lưu thẳng vào CSDL PostgreSQL)
                </div>
                <div style="font-size: 12px; color: #64748b;">
                    Hỗ trợ tệp .html độc lập (Single-file). Khi tải lên, toàn bộ nội dung HTML sẽ được đọc và lưu trực tiếp vào cơ sở dữ liệu PostgreSQL.
                </div>
            </div>

            <div class="html-dropzone" id="html-dropzone">
                <div style="font-size: 32px; margin-bottom: 6px;">📄</div>
                <div style="font-weight: 600; font-size: 13.5px; color: #0284c7; margin-bottom: 4px;">
                    Kéo & thả tệp .html vào đây hoặc bấm để chọn tệp từ máy tính
                </div>
                <div style="font-size: 11.5px; color: #64748b;">
                    Tệp sẽ được đọc ngay lập tức và xem trước trong trình duyệt (Dung lượng tối đa ≤ 5MB).
                </div>
                <input type="file" id="html-local-picker" accept=".html" style="display: none;">
            </div>

            <div id="html-db-status-box"></div>
        `;

        if (uploadRow) {
            uploadRow.parentElement.insertBefore(card, uploadRow);
            uploadRow.style.display = 'none'; // Ẩn trường upload thô
        } else {
            htmlRow.parentElement.insertBefore(card, htmlRow);
        }

        // Đặt chiều cao hợp lý cho textarea mã nguồn HTML nếu cần xem mã
        contentHtmlTextarea.style.minHeight = '140px';

        const dropzone = card.querySelector('#html-dropzone');
        const localPicker = card.querySelector('#html-local-picker');
        const statusBox = card.querySelector('#html-db-status-box');

        function renderHtmlPreviewFromContent(htmlContent, fileName) {
            if (!htmlContent || !htmlContent.trim()) {
                statusBox.innerHTML = '';
                return;
            }
            const sizeKb = (new Blob([htmlContent]).size / 1024).toFixed(1);
            statusBox.innerHTML = `
                <div class="html-current-file-box">
                    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="background: #ecfdf5; color: #047857; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 4px; border: 1px solid #a7f3d0;">
                                💾 DỮ LIỆU TRONG CSDL
                            </span>
                            <span style="font-size: 12px; font-weight: 600; color: #0f172a;">
                                ${fileName ? fileName : 'Nội dung HTML'} (${sizeKb} KB)
                            </span>
                        </div>
                        <button type="button" id="btn-refresh-html-preview" style="font-size: 11.5px; font-weight: 600; color: #0284c7; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 3px 10px; cursor: pointer;">
                            🔄 Làm mới xem trước
                        </button>
                    </div>
                    <div>
                        <div style="font-size: 11px; font-weight: 600; color: #64748b; margin-bottom: 4px;">
                            Xem trước hiển thị (Iframe Sandbox từ CSDL):
                        </div>
                        <iframe id="admin-html-preview-frame" class="html-preview-frame" sandbox="allow-scripts"></iframe>
                    </div>
                </div>
            `;

            const iframe = statusBox.querySelector('#admin-html-preview-frame');
            if (iframe) {
                iframe.srcdoc = htmlContent;
            }

            const refreshBtn = statusBox.querySelector('#btn-refresh-html-preview');
            if (refreshBtn && iframe) {
                refreshBtn.addEventListener('click', () => {
                    iframe.srcdoc = contentHtmlTextarea.value;
                });
            }
        }

        // Khởi tạo xem trước nếu bài đã có nội dung trong CSDL
        if (contentHtmlTextarea.value && contentHtmlTextarea.value.trim()) {
            renderHtmlPreviewFromContent(contentHtmlTextarea.value.trim());
        }

        // Lắng nghe chỉnh sửa trực tiếp trên textarea
        contentHtmlTextarea.addEventListener('input', function () {
            const iframe = statusBox.querySelector('#admin-html-preview-frame');
            if (iframe) {
                iframe.srcdoc = this.value;
            } else if (this.value.trim()) {
                renderHtmlPreviewFromContent(this.value.trim());
            }
        });

        dropzone.addEventListener('click', () => localPicker.click());

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            if (e.dataTransfer && e.dataTransfer.files.length > 0) {
                loadHtmlFileContent(e.dataTransfer.files[0]);
            }
        });

        localPicker.addEventListener('change', (e) => {
            if (e.target.files && e.target.files.length > 0) {
                loadHtmlFileContent(e.target.files[0]);
            }
        });

        function loadHtmlFileContent(file) {
            if (!file.name.toLowerCase().endsWith('.html')) {
                alert('Chỉ chấp nhận tệp có đuôi mở rộng .html');
                return;
            }
            if (file.size > 5 * 1024 * 1024) {
                alert('Dung lượng tệp vượt quá 5MB. Vui lòng kiểm tra lại.');
                return;
            }

            dropzone.innerHTML = `
                <div style="font-size: 26px; margin-bottom: 6px;">⏳</div>
                <div style="font-weight: 600; font-size: 13px; color: #0284c7;">
                    Đang nạp ${file.name} vào bộ nhớ...
                </div>
            `;

            const reader = new FileReader();
            reader.onload = function (event) {
                const text = event.target.result;
                contentHtmlTextarea.value = text;

                // Tự động chuyển đổi định dạng tài liệu sang HTML
                if (contentTypeSelect) {
                    contentTypeSelect.value = 'HTML';
                    syncContentTypeUI();
                }

                // Đồng bộ file vào input form upload nếu có
                if (uploadHtmlInput) {
                    try {
                        const dataTransfer = new DataTransfer();
                        dataTransfer.items.add(file);
                        uploadHtmlInput.files = dataTransfer.files;
                    } catch (err) {}
                }

                dropzone.innerHTML = `
                    <div style="font-size: 26px; margin-bottom: 6px;">✅</div>
                    <div style="font-weight: 600; font-size: 13.5px; color: #16a34a;">
                        Đã nạp tệp: <b>${file.name}</b> (${(file.size / 1024).toFixed(1)} KB)
                    </div>
                    <div style="font-size: 11.5px; color: #64748b; margin-top: 4px;">
                        Nội dung đã được ghi vào trường CSDL. Bấm <b>Lưu</b> để hoàn tất lưu trữ vào PostgreSQL!
                    </div>
                    <input type="file" id="html-local-picker" accept=".html" style="display: none;">
                `;

                card.querySelector('#html-local-picker').addEventListener('change', (e) => {
                    if (e.target.files && e.target.files.length > 0) {
                        loadHtmlFileContent(e.target.files[0]);
                    }
                });

                renderHtmlPreviewFromContent(text, file.name);
            };

            reader.onerror = function () {
                alert('Lỗi đọc tệp từ đĩa cục bộ');
            };

            reader.readAsText(file, 'UTF-8');
        }
    }
});
