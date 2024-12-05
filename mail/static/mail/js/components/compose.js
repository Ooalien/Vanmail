export function compose_email() {
    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#single-email').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';

    // Clear out composition fields
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
    document.querySelector('#compose-attachments').value = '';
    document.querySelector('#compose-attachments-preview').innerHTML = '';
}

export function reply_email(email) {
    // Show compose view
    compose_email();

    // Pre-fill composition fields
    document.querySelector('#compose-recipients').value = email.sender;
    
    let subject = email.subject;
    if (!subject.startsWith('Re: ')) {
        subject = 'Re: ' + subject;
    }
    document.querySelector('#compose-subject').value = subject;
    
    document.querySelector('#compose-body').value = 
        `\n\nOn ${email.timestamp} ${email.sender} wrote:\n${email.body}`;
}

// Handle attachment preview
document.querySelector('#compose-attachments')?.addEventListener('change', function(e) {
    const preview = document.querySelector('#compose-attachments-preview');
    preview.innerHTML = '';
    
    Array.from(this.files).forEach(file => {
        const item = document.createElement('div');
        item.className = 'preview-attachment-item';
        item.innerHTML = `
            <i class="fas fa-file"></i>
            <span>${file.name}</span>
            <span class="remove-preview">&times;</span>
        `;
        preview.appendChild(item);
    });
}); 