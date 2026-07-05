document.addEventListener('DOMContentLoaded',()=>{
  // Frost the sticky nav once the page is scrolled. (Reveal is pure CSS.)
  const nav=document.getElementById('nav');
  const onScroll=()=>nav.classList.toggle('frost',window.scrollY>12);
  onScroll(); window.addEventListener('scroll',onScroll,{passive:true});

  // Render the four theme panels by cloning the hero panel (one source of truth).
  const hero=document.querySelector('#hero .ccm');
  if(hero){
    document.querySelectorAll('.theme-card[data-ccm]').forEach(fig=>{
      const p=hero.cloneNode(true);
      p.className='ccm '+fig.dataset.ccm;
      p.removeAttribute('role'); p.removeAttribute('aria-label');
      p.setAttribute('aria-hidden','true');
      fig.insertBefore(p, fig.firstChild);
    });
  }

  // Respect reduced-motion: don't autoplay the demo — show its poster frame instead.
  const demo=document.querySelector('.demo-vid');
  if(demo && window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    demo.removeAttribute('autoplay');
    demo.load(); // reset to the static poster
  }
});
