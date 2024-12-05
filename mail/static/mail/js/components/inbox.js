export function load_mailbox(mailbox) {
    // Show the mailbox and hide other views
    document.querySelector('#emails-view').style.display = 'block';
    document.querySelector('#single-email').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';

    // Show the mailbox name and clear existing emails
    document.querySelector('#emails-view').innerHTML = `
        <div class="mailbox-header">
            <h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>
        </div>
        <div class="email-list"></div>
    `;

    // Load emails
    fetch(`/emails/${mailbox}`)
    .then(response => response.json())
    .then(emails => {
        const emailList = document.querySelector('.email-list');
        
        if (emails.length === 0) {
            emailList.innerHTML = `
                <div class="no-emails">
                    <i class="fas fa-inbox"></i>
                    <p>No emails in ${mailbox}</p>
                </div>
            `;
            return;
        }

        // Clear any existing emails first
        emailList.innerHTML = '';

        emails.forEach(email => {
            const emailElement = document.createElement('div');
            emailElement.className = `email-item ${!email.read ? 'unread' : ''}`;
            
            // Different layout for sent vs other mailboxes
            if (mailbox === 'sent') {
                emailElement.innerHTML = `
                    <div class="email-recipients">To: ${email.recipients.join(', ')}</div>
                    <div class="email-content">
                        <div class="email-subject">${email.subject}</div>
                        ${email.attachments && email.attachments.length > 0 ? 
                            `<div class="email-attachment-indicator">
                                <i class="fas fa-paperclip" title="${email.attachments.length} attachment(s)"></i>
                                <span class="attachment-count">${email.attachments.length}</span>
                            </div>` : ''
                        }
                    </div>
                    <div class="email-timestamp">${email.timestamp}</div>
                    <div class="email-actions">
                        <button class="action-btn view-btn" title="View Email">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${email.attachments && email.attachments.length > 0 ? 
                            `<div class="attachments-dropdown">
                                <button class="action-btn attachments-btn" title="Download Attachments">
                                    <i class="fas fa-paperclip"></i>
                                </button>
                                <div class="attachments-list">
                                    ${email.attachments.map(att => `
                                        <a href="/attachment/${att.id}" 
                                           class="attachment-download-link"
                                           download="${att.filename}">
                                            <i class="fas fa-file"></i>
                                            ${att.filename}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>` : ''
                        }
                    </div>
                `;
            } else {
                emailElement.innerHTML = `
                    <div class="email-sender">${email.sender}</div>
                    <div class="email-content">
                        <div class="email-subject">${email.subject}</div>
                        ${email.attachments && email.attachments.length > 0 ? 
                            `<div class="email-attachment-indicator">
                                <i class="fas fa-paperclip" title="${email.attachments.length} attachment(s)"></i>
                                <span class="attachment-count">${email.attachments.length}</span>
                            </div>` : ''
                        }
                    </div>
                    <div class="email-timestamp">${email.timestamp}</div>
                    <div class="email-actions">
                        <button class="action-btn view-btn" title="View Email">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${email.attachments && email.attachments.length > 0 ? 
                            `<div class="attachments-dropdown">
                                <button class="action-btn attachments-btn" title="Download Attachments">
                                    <i class="fas fa-paperclip"></i>
                                </button>
                                <div class="attachments-list">
                                    ${email.attachments.map(att => `
                                        <a href="/attachment/${att.id}" 
                                           class="attachment-download-link"
                                           download="${att.filename}">
                                            <i class="fas fa-file"></i>
                                            ${att.filename}
                                        </a>
                                    `).join('')}
                                </div>
                            </div>` : ''
                        }
                        ${mailbox === 'inbox' ? `
                            <button class="action-btn archive-btn" title="Archive">
                                <i class="fas fa-archive"></i>
                            </button>
                        ` : ''}
                        ${mailbox === 'archive' ? `
                            <button class="action-btn unarchive-btn" title="Unarchive">
                                <i class="fas fa-inbox"></i>
                            </button>
                        ` : ''}
                    </div>
                `;
            }

            // Add click handler to entire email item
            emailElement.addEventListener('click', function(e) {
                // Don't trigger if clicking action buttons
                if (!e.target.closest('.action-btn')) {
                    load_email(email.id);
                }
            });

            // Add click handlers for action buttons
            const viewBtn = emailElement.querySelector('.view-btn');
            if (viewBtn) {
                viewBtn.onclick = (e) => {
                    e.stopPropagation();
                    load_email(email.id);
                };
            }
            
            const archiveBtn = emailElement.querySelector('.archive-btn');
            if (archiveBtn) {
                archiveBtn.onclick = (e) => {
                    e.stopPropagation();
                    archive_email(email.id, true);
                };
            }

            const unarchiveBtn = emailElement.querySelector('.unarchive-btn');
            if (unarchiveBtn) {
                unarchiveBtn.onclick = (e) => {
                    e.stopPropagation();
                    archive_email(email.id, false);
                };
            }

            // Add event listeners for attachments dropdown
            const attachmentsBtn = emailElement.querySelector('.attachments-btn');
            if (attachmentsBtn) {
                attachmentsBtn.onclick = (e) => {
                    e.stopPropagation();
                    const dropdown = e.target.closest('.attachments-dropdown');
                    dropdown.classList.toggle('active');
                };
            }

            emailList.appendChild(emailElement);
        });
    })
    .catch(error => {
        console.error('Error:', error);
        document.querySelector('.email-list').innerHTML = `
            <div class="alert alert-danger">
                Error loading emails: ${error.message}
            </div>
        `;
    });
} 