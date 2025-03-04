// main.js - Kindergarten Daily Report Generator

document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const form = document.querySelector('form');
    const contentInput = document.getElementById('content');
    const fileInput = document.getElementById('images');
    const filePreview = document.getElementById('file-preview');
    
    // Handle file input change for preview
    if (fileInput && filePreview) {
        fileInput.addEventListener('change', function() {
            // Clear previous previews
            filePreview.innerHTML = '';
            
            if (this.files && this.files.length > 0) {
                // Update the label to show number of files selected
                const fileUploadLabel = document.querySelector('.file-upload-label');
                if (fileUploadLabel) {
                    fileUploadLabel.textContent = `已選擇 ${this.files.length} 張照片`;
                }
                
                // Create preview for each file
                Array.from(this.files).forEach((file, index) => {
                    if (!file.type.match('image.*')) {
                        return;
                    }
                    
                    const reader = new FileReader();
                    
                    reader.onload = function(e) {
                        const previewItem = document.createElement('div');
                        previewItem.className = 'preview-item';
                        previewItem.dataset.index = index;
                        
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.alt = file.name;
                        
                        const removeButton = document.createElement('div');
                        removeButton.className = 'remove-preview';
                        removeButton.innerHTML = '×';
                        removeButton.addEventListener('click', function(e) {
                            e.stopPropagation();
                            // We can't actually remove files from a file input,
                            // so we'll just hide the preview and mark it for exclusion
                            previewItem.style.display = 'none';
                            previewItem.dataset.excluded = 'true';
                            
                            // Update count of visible previews
                            updateFileCount();
                        });
                        
                        previewItem.appendChild(img);
                        previewItem.appendChild(removeButton);
                        filePreview.appendChild(previewItem);
                    };
                    
                    reader.readAsDataURL(file);
                });
            } else {
                // Reset the label if no files selected
                const fileUploadLabel = document.querySelector('.file-upload-label');
                if (fileUploadLabel) {
                    fileUploadLabel.textContent = '選擇照片';
                }
            }
        });
        
        // Function to update file count display
        function updateFileCount() {
            const visiblePreviews = Array.from(filePreview.children).filter(
                item => item.style.display !== 'none'
            ).length;
            
            const fileUploadLabel = document.querySelector('.file-upload-label');
            if (fileUploadLabel) {
                if (visiblePreviews > 0) {
                    fileUploadLabel.textContent = `已選擇 ${visiblePreviews} 張照片`;
                } else {
                    fileUploadLabel.textContent = '選擇照片';
                }
            }
        }
    }
    
    if (form) {
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Validate content
            if (!contentInput.value.trim()) {
                showValidationError(contentInput, '請輸入課堂內容！');
                isValid = false;
            }
            
            if (!isValid) {
                event.preventDefault();
            } else {
                // Show loading state
                showLoading();
            }
        });
    }
    
    // Input validation on blur
    if (contentInput) {
        contentInput.addEventListener('blur', function() {
            if (!this.value.trim()) {
                showValidationError(this, '請輸入課堂內容！');
            } else {
                clearValidationError(this);
            }
        });
    }
    
    // UI feedback functions
    function showValidationError(inputElement, message) {
        clearValidationError(inputElement);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'validation-error';
        errorDiv.textContent = message;
        errorDiv.style.color = '#ef476f';
        errorDiv.style.marginTop = '8px';
        errorDiv.style.fontSize = '0.9em';
        
        if (inputElement.parentNode) {
            inputElement.parentNode.appendChild(errorDiv);
            inputElement.style.borderColor = '#ef476f';
        }
    }
    
    function clearValidationError(inputElement) {
        if (inputElement.parentNode) {
            const errorDiv = inputElement.parentNode.querySelector('.validation-error');
            if (errorDiv) {
                errorDiv.remove();
            }
            inputElement.style.borderColor = '#06d6a0';
        }
    }
    
    function showLoading() {
        const submitButton = document.querySelector('.btn');
        if (submitButton) {
            submitButton.innerHTML = '生成中... <span class="loading-spinner">🔄</span>';
            submitButton.disabled = true;
            
            // Add spinning animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .loading-spinner {
                    display: inline-block;
                    animation: spin 2s linear infinite;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    // Add cute animations
    animatePageElements();
    
    // Print functionality for success page
    const printButton = document.getElementById('printReport');
    if (printButton) {
        printButton.addEventListener('click', function() {
            window.print();
        });
    }
});

// Cute animations for page elements
function animatePageElements() {
    // Add a subtle bounce to emojis
    const emojis = document.querySelectorAll('.cute-icon, .header-image span');
    
    emojis.forEach(emoji => {
        emoji.style.display = 'inline-block';
        emoji.style.transition = 'transform 0.3s ease';
        
        emoji.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.2)';
        });
        
        emoji.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });
}
