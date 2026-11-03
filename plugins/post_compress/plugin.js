// 示例插件前端：头部"压缩 开/关"按钮，切换服务端后处理器开关
(function () {
  let on = false;
  function render() {
    const b = document.getElementById('pcbtn');
    if (b) { b.classList.toggle('on', on); b.textContent = '压缩:' + (on ? '开' : '关'); }
  }
  const btn = window.ZZDM.addHeaderButton('压缩:关', async function () {
    on = !on;
    await window.ZZDM.api('/api/plugins/post_compress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: on })
    });
    render();
  });
  btn.id = 'pcbtn';
  // 启动时同步服务端开关状态
  window.ZZDM.api('/api/plugins').then(function (d) {
    const p = (d.processors || []).find(function (x) { return x.id === 'post_compress'; });
    if (p) { on = !!p.enabled; render(); }
  });
})();
