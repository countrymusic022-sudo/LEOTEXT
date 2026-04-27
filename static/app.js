const fileInput = document.getElementById('fileInput');
const startBtn = document.getElementById('startBtn');
const statusText = document.getElementById('status');
const downloadLink = document.getElementById('downloadLink');
const preview = document.getElementById('preview');

startBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) {
    statusText.textContent = '請先選擇檔案';
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  startBtn.disabled = true;
  statusText.textContent = '上傳中，請稍候...';
  downloadLink.classList.add('hidden');
  preview.value = '';

  try {
    const response = await fetch('/api/transcribe', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || '轉換失敗');
    }

    statusText.textContent = '轉換完成，可下載 SRT';
    preview.value = data.preview || '';
    downloadLink.href = data.download_url;
    downloadLink.classList.remove('hidden');
  } catch (error) {
    statusText.textContent = `錯誤：${error.message}`;
  } finally {
    startBtn.disabled = false;
  }
});
