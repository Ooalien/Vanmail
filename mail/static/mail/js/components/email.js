export function load_email(id) {
    fetch(`/emails/${id}`)
    .then(response => response.json())
    .then(email => {
        console.log("Loading email:", email);

        // Show email view
        document.querySelector('#emails-view').style.display = 'none';
        document.querySelector('#compose-view').style.display = 'none';
        
        const emailView = document.querySelector('#single-email');
        emailView.style.display = 'block';

        // Build email HTML
        let emailHTML = `
            <div class="email-detail-card">
                <div class="email-detail-header">
                    <h4>${email.subject}</h4>
                    <div class="email-detail-actions">
                        <button class="btn btn-outline-primary reply-btn">
                            <i class="fas fa-reply"></i> Reply
                        </button>
                        <button class="btn btn-outline-primary archive-btn">
                            <i class="fas fa-archive"></i> 
                            ${email.archived ? 'Unarchive' : 'Archive'}
                        </button>
                    </div>
                </div>
                
                <div class="email-detail-meta">
                    <div><strong>From:</strong> ${email.sender}</div>
                    <div><strong>To:</strong> ${email.recipients.join(', ')}</div>
                    <div><strong>Date:</strong> ${email.timestamp}</div>
                </div>

                <div class="email-detail-body">
                    ${email.body}
                </div>`;

        // Add attachments section if there are any
        if (email.attachments && email.attachments.length > 0) {
            emailHTML += `
                <div class="email-attachments">
                    <div class="attachments-header">
                        <i class="fas fa-paperclip"></i>
                        <strong>Attachments (${email.attachments.length})</strong>
                    </div>
                    <div class="attachment-list">`;
            
            email.attachments.forEach(att => {
                emailHTML += `
                    <div class="attachment-item">
                        <div class="attachment-info">
                            <i class="fas fa-file"></i>
                            <span class="attachment-name">${att.filename}</span>
                        </div>
                        <div class="attachment-actions">
                            <a href="/attachment/${att.id}" 
                               class="btn btn-sm btn-primary"
                               download>
                                <i class="fas fa-download"></i>
                                Download
                            </a>
                        </div>
                    </div>`;
            });

            emailHTML += `
                    </div>
                </div>`;
        }

        emailHTML += `</div>`;
        emailView.innerHTML = emailHTML;

        // Add event listeners
        emailView.querySelector('.reply-btn').onclick = () => reply_email(email);
        emailView.querySelector('.archive-btn').onclick = () => {
            archive_email(email.id, !email.archived)
                .then(() => load_mailbox('inbox'));
        };

        // Mark as read
        if (!email.read) {
            fetch(`/emails/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ read: true })
            });
        }
    });
} 