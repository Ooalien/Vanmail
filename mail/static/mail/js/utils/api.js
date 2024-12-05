export async function fetchEmails(mailbox) {
    const response = await fetch(`/emails/${mailbox}`);
    return response.json();
}

export async function sendEmail(formData) {
    const response = await fetch('/emails', {
        method: 'POST',
        body: formData
    });
    return response.json();
}

export async function archiveEmail(id, shouldArchive) {
    const response = await fetch(`/emails/${id}`, {
        method: 'PUT',
        body: JSON.stringify({
            archived: shouldArchive
        })
    });
    return response.ok;
} 