document.addEventListener('DOMContentLoaded', function () {
    // 1. Mermaid Diagrams
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'neutral',
            securityLevel: 'loose'
        });
    }

    // 2. In ấn / Xuất PDF
    const printBtns = document.querySelectorAll('.btn-print-document');
    printBtns.forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            window.print();
        });
    });

    // 3. Sao chép liên kết quy trình
    const copyLinkBtn = document.getElementById('btn-copy-link');
    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', function () {
            navigator.clipboard.writeText(window.location.href).then(() => {
                const orig = copyLinkBtn.innerHTML;
                copyLinkBtn.innerHTML = '<span>✅ Đã chép</span>';
                setTimeout(() => { copyLinkBtn.innerHTML = orig; }, 2000);
            });
        });
    }

    // 4. Scroll Spy Mục lục (TOC)
    const tocLinks = document.querySelectorAll('.toc a');
    if (tocLinks.length > 0) {
        const headings = [];
        tocLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#')) {
                const targetId = decodeURIComponent(href.slice(1));
                const targetElem = document.getElementById(targetId);
                if (targetElem) headings.push({ link, targetElem });
            }
        });

        window.addEventListener('scroll', function () {
            let current = null;
            const scrollPos = window.scrollY + 100;
            for (let i = 0; i < headings.length; i++) {
                if (headings[i].targetElem.offsetTop <= scrollPos) {
                    current = headings[i].link;
                }
            }
            tocLinks.forEach(l => l.classList.remove('text-slate-900', 'font-semibold', 'underline'));
            if (current) current.classList.add('text-slate-900', 'font-semibold', 'underline');
        });
    }
});
