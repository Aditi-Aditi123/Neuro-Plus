document.addEventListener("DOMContentLoaded", () => {

    const toggleViewBtn = document.getElementById('toggleViewBtn');
    if (toggleViewBtn) {
        toggleViewBtn.addEventListener('click', () => {
            const isToParent = toggleViewBtn.innerText.includes('Parent');
            if (isToParent) {
                const pinModal = new bootstrap.Modal(document.getElementById('pinModal'));
                pinModal.show();

                document.getElementById('submitPinBtn').onclick = () => {
                    const pin = document.getElementById('pinInput').value;
                    fetch('/toggle_view', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ pin: pin })
                    }).then(res => res.json()).then(data => {
                        if (data.success) {
                            window.location.reload();
                        } else {
                            document.getElementById('pinError').innerText = data.error || 'Invalid PIN.';
                            document.getElementById('pinError').classList.remove('d-none');
                        }
                    });
                };
            } else {
                fetch('/toggle_view', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ pin: '' })
                }).then(res => res.json()).then(data => {
                    if (data.success) window.location.reload();
                });
            }
        });
    }

    let selectedSticker = null;
    let fileObj = null;

    const photoUpload = document.getElementById('photoUpload');
    if (photoUpload) {
        photoUpload.addEventListener('change', function (e) {
            if (e.target.files && e.target.files[0]) {
                fileObj = e.target.files[0];

                const reader = new FileReader();
                reader.onload = function (e) {
                    document.getElementById('previewImg').src = e.target.result;
                    document.getElementById('uploadPreview').classList.remove('d-none');
                    document.getElementById('stickerTray').classList.remove('d-none');
                }
                reader.readAsDataURL(fileObj);
            }
        });
    }

    const stickerBtns = document.querySelectorAll('.sticker-btn');
    stickerBtns.forEach(btn => {
        btn.addEventListener('click', function () {

            stickerBtns.forEach(b => b.classList.remove('btn-warning'));
            stickerBtns.forEach(b => b.classList.add('btn-light'));

            this.classList.remove('btn-light');
            this.classList.add('btn-warning');

            selectedSticker = this.innerText;

            const previewStext = document.getElementById('previewSticker');
            previewStext.innerText = selectedSticker;
            previewStext.style.display = 'block';

            document.getElementById('submitQuestBtn').classList.remove('d-none');
            document.getElementById('submitQuestBtn').disabled = false;
        });
    });

    const submitQuestBtn = document.getElementById('submitQuestBtn');
    if (submitQuestBtn) {
        submitQuestBtn.addEventListener('click', () => {
            submitQuestBtn.disabled = true;
            submitQuestBtn.innerText = "Uploading...";

            const quest_id = document.querySelector('input[name="quest_id"]').value;
            const formData = new FormData();
            formData.append('file', fileObj);
            formData.append('quest_id', quest_id);
            formData.append('sticker', selectedSticker || '⭐');

            fetch('/upload', {
                method: 'POST',
                body: formData
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    alert("Quest Sealed! Pending Review.");
                    window.location.reload();
                } else {
                    alert("Error: " + data.error);
                    submitQuestBtn.disabled = false;
                    submitQuestBtn.innerText = "Submit Quest!";
                }
            }).catch(err => {
                console.error(err);
                submitQuestBtn.disabled = false;
            });
        });
    }

    const addTaskForm = document.getElementById('addTaskForm');
    if (addTaskForm) {
        addTaskForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const title = document.getElementById('newTaskTitle').value;
            const desc = document.getElementById('newTaskDesc').value;
            const icon = document.getElementById('newTaskIcon').value;
            const xp = document.getElementById('newTaskXP').value;

            fetch('/add_quest_endpoint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description: desc, icon, xp })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert('Failed to add task: ' + data.error);
                    }
                });
        });
    }

    const removeTaskBtns = document.querySelectorAll('.remove-task-btn');
    removeTaskBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            if (!confirm("Are you sure you want to remove this task?")) return;
            const questId = this.getAttribute('data-quest-id');
            fetch('/remove_quest_endpoint', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ quest_id: questId })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload();
                    } else {
                        alert('Failed to remove task.');
                    }
                });
        });
    });

    const approveBtns = document.querySelectorAll('.btn-approve');
    approveBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const subId = this.getAttribute('data-sub-id');
            document.getElementById(`submission-${subId}`).style.opacity = '0.5';
            this.innerText = 'Approving...';

            fetch('/approve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sub_id: subId })
            }).then(res => res.json()).then(data => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert("Failed to approve.");
                    document.getElementById(`submission-${subId}`).style.opacity = '1';
                }
            });
        });
    });

});
