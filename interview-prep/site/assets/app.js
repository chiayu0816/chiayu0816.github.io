(function(){
  "use strict";
  var DATA = window.__IP_DATA__ || {techs:[],total:0};
  var LS = "ipv1:";
  var $ = function(s,r){return (r||document).querySelector(s);};
  var ce = function(t,c){var e=document.createElement(t); if(c) e.className=c; return e;};
  var techByKey = {};
  DATA.techs.forEach(function(t){ techByKey[t.key] = t; });

  // ---- progress store ----
  function isDone(id){ return localStorage.getItem(LS+id)==="1"; }
  function setDone(id,v){ v?localStorage.setItem(LS+id,"1"):localStorage.removeItem(LS+id); }

  var sideNav = $("#side-nav"), content = $("#content");
  var navItems = {};
  var bnCurrent = $("#bn-current");

  function headerOffset(){
    var tb = $(".topbar");
    return (tb ? tb.getBoundingClientRect().height : 74) + 10;
  }

  function isMobileNav(){ return window.matchMedia("(max-width: 899px)").matches; }

  function setNavOpen(open){
    document.body.classList.toggle("nav-open", open);
    var toggle = $("#nav-toggle");
    var backdrop = $("#nav-backdrop");
    if(toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if(backdrop) backdrop.hidden = !open;
  }

  function setActiveTech(key){
    Object.keys(navItems).forEach(function(k){ navItems[k].classList.toggle("active", k===key); });
    var tech = techByKey[key];
    if(bnCurrent && tech) bnCurrent.textContent = tech.name;
  }

  // ---- render ----
  DATA.techs.forEach(function(tech, ti){
    // nav
    var n = ce("button","nav-item p"+tech.prio);
    n.dataset.key = tech.key;
    n.innerHTML = '<span class="dot"></span><span class="nm">'+tech.name+
      '</span><span class="ct" data-ct>0/'+tech.count+'</span>';
    n.addEventListener("click",function(){
      scrollToTech(tech.key);
      if(isMobileNav()) setNavOpen(false);
    });
    sideNav.appendChild(n);
    navItems[tech.key] = n;

    // section
    var sec = ce("section","tech");
    sec.id = "tech-"+tech.key;
    var head = ce("div","tech-head");
    head.innerHTML = '<span class="idx">'+String(ti+1).padStart(2,"0")+'</span>'+
      '<h2>'+tech.name+'</h2>'+
      '<span class="meta" data-meta>0 / '+tech.count+' 已複習</span>'+
      '<span class="bar"><i data-prog></i></span>';
    sec.appendChild(head);

    tech.topics.forEach(function(t, idx){
      sec.appendChild(buildCard(tech, t, idx));
    });
    content.appendChild(sec);
  });

  function buildCard(tech, t, idx){
    var id = tech.key+"-"+idx;
    var card = ce("article","card");
    card.id = "c-"+id;
    card.style.animationDelay = Math.min(idx,12)*22 + "ms";
    if(isDone(id)) card.classList.add("reviewed");

    var row = ce("button","q-row");
    row.setAttribute("aria-expanded","false");
    row.innerHTML = '<span class="q-num">'+String(idx+1).padStart(2,"0")+'</span>'+
      '<span class="q-text"></span>'+
      '<label class="rev" title="標記為已複習"><input type="checkbox"'+
      (isDone(id)?" checked":"")+' aria-label="標記為已複習"><span>已複習</span></label>'+
      '<span class="chev" aria-hidden="true">▶</span>';
    $(".q-text",row).textContent = t.q;
    row.addEventListener("click",function(e){
      if(e.target.closest(".rev")) return;
      var open = card.classList.toggle("open");
      row.setAttribute("aria-expanded", open ? "true" : "false");
    });

    var chk = $(".rev input",row);
    chk.addEventListener("click",function(e){ e.stopPropagation(); });
    chk.addEventListener("change",function(){
      setDone(id, chk.checked);
      card.classList.toggle("reviewed", chk.checked);
      updateProgress();
    });
    card.appendChild(row);

    var ans = ce("div","answer");
    ans.innerHTML = renderAnswer(t);
    card.appendChild(ans);
    card._text = t.text;
    card._q = t.q;
    return card;
  }

  function sec(cls,label,inner){
    return '<div class="sec sec-'+cls+'"><span class="sec-label">'+label+'</span>'+inner+'</div>';
  }
  function list(arr){ return "<ul>"+arr.map(function(x){return "<li>"+x+"</li>";}).join("")+"</ul>"; }

  function renderAnswer(t){
    var h = "";
    if(t.core) h += sec("core","核心回答",t.core);
    if((t.dive&&t.dive.length) || t.diagram)
      h += sec("dive","深入原理",(t.dive&&t.dive.length?list(t.dive):"")+(t.diagram||""));
    if(t.followups&&t.followups.length){
      var fu = t.followups.map(function(f){
        return '<div class="fu"><div class="fq">'+f.q+'</div><div class="fa">'+f.a+'</div></div>';
      }).join("");
      h += sec("ask","考官可能追問",fu);
    }
    if(t.pitfalls&&t.pitfalls.length) h += sec("trap","常見陷阱 / 易錯點",list(t.pitfalls));
    if(t.resume) h += sec("resume","結合履歷",t.resume);
    return h;
  }

  // ---- progress ----
  function updateProgress(){
    var totalDone = 0;
    DATA.techs.forEach(function(tech){
      var done = 0;
      tech.topics.forEach(function(_,idx){ if(isDone(tech.key+"-"+idx)) done++; });
      totalDone += done;
      var nav = navItems[tech.key];
      $("[data-ct]",nav).textContent = done+"/"+tech.count;
      nav.classList.toggle("done", done===tech.count && tech.count>0);
      var s = $("#tech-"+tech.key);
      $("[data-meta]",s).textContent = done+" / "+tech.count+" 已複習";
      $("[data-prog]",s).style.width = (tech.count? (done/tech.count*100):0)+"%";
    });
    var pct = DATA.total? Math.round(totalDone/DATA.total*100):0;
    $("#p-done").textContent = totalDone;
    $("#p-total").textContent = DATA.total;
    $("#p-pct").textContent = pct+"%";
    $("#ring").style.setProperty("--p", pct);
    var ringBottom = $("#ring-bottom");
    if(ringBottom) ringBottom.style.setProperty("--p", pct);
  }

  // ---- scrollspy ----
  function scrollToTech(key){
    var el = $("#tech-"+key);
    if(el) window.scrollTo({top: el.getBoundingClientRect().top + window.pageYOffset - headerOffset(), behavior:"smooth"});
  }
  var io = new IntersectionObserver(function(entries){
    entries.forEach(function(en){
      if(en.isIntersecting){
        var key = en.target.id.replace("tech-","");
        setActiveTech(key);
      }
    });
  },{rootMargin:"-40% 0px -48% 0px"});
  DATA.techs.forEach(function(t){ io.observe($("#tech-"+t.key)); });
  if(DATA.techs[0]) setActiveTech(DATA.techs[0].key);

  // ---- mobile nav ----
  var navToggle = $("#nav-toggle");
  var navBackdrop = $("#nav-backdrop");
  if(navToggle){
    navToggle.addEventListener("click",function(){
      setNavOpen(!document.body.classList.contains("nav-open"));
    });
  }
  if(navBackdrop){
    navBackdrop.addEventListener("click",function(){ setNavOpen(false); });
  }
  var bnMenu = $("#bn-menu");
  var bnSearch = $("#bn-search");
  if(bnMenu) bnMenu.addEventListener("click",function(){ setNavOpen(true); });
  if(bnSearch){
    bnSearch.addEventListener("click",function(){
      var box = $("#search");
      if(box){
        box.focus();
        window.scrollTo({top:0, behavior:"smooth"});
      }
    });
  }
  document.addEventListener("keydown",function(e){
    if(e.key==="Escape"){
      if(document.body.classList.contains("nav-open")) setNavOpen(false);
    }
  });

  // ---- search ----
  var box = $("#search");
  var timer=null;
  box.addEventListener("input",function(){ clearTimeout(timer); timer=setTimeout(runSearch,120); });
  box.addEventListener("keydown",function(e){ if(e.key==="Escape"){ box.value=""; runSearch(); box.blur(); } });
  document.addEventListener("keydown",function(e){
    if(e.key==="/" && document.activeElement!==box && !isMobileNav()){
      e.preventDefault(); box.focus();
    }
  });

  function esc(s){ return s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&"); }
  function runSearch(){
    var q = box.value.trim().toLowerCase();
    var any = false;
    DATA.techs.forEach(function(tech){
      var s = $("#tech-"+tech.key);
      var shown = 0;
      Array.prototype.forEach.call(s.querySelectorAll(".card"),function(card){
        var match = !q || card._text.indexOf(q) !== -1;
        card.classList.toggle("hidden", !match);
        if(match){
          shown++; any=true;
          var qt = $(".q-text",card);
          var row = $(".q-row",card);
          if(q){
            qt.innerHTML = card._q.replace(new RegExp("("+esc(box.value.trim())+")","ig"),"<mark>$1</mark>");
            card.classList.add("open");
            if(row) row.setAttribute("aria-expanded","true");
          } else {
            qt.textContent = card._q;
            card.classList.remove("open");
            if(row) row.setAttribute("aria-expanded","false");
          }
        }
      });
      s.classList.toggle("hidden", shown===0 && !!q);
    });
    $("#empty").classList.toggle("hidden", any || !q);
  }

  // reset progress
  $("#reset").addEventListener("click",function(){
    if(confirm("清除所有「已複習」紀錄？")){
      Object.keys(localStorage).forEach(function(k){ if(k.indexOf(LS)===0) localStorage.removeItem(k); });
      Array.prototype.forEach.call(document.querySelectorAll(".rev input"),function(i){ i.checked=false; });
      Array.prototype.forEach.call(document.querySelectorAll(".card"),function(c){ c.classList.remove("reviewed"); });
      updateProgress();
    }
  });

  updateProgress();
})();
