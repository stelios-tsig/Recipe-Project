import customtkinter as ctk
from PIL import Image, ImageDraw
import os
import sys
from Model import RecipeManager

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("dark-blue")

CATEGORIES   = ["Ψάρια", "Ζυμαρικά", "Κρέας", "Φούρνος", "Air Fryer", "Vegan"]
DIFFICULTIES = ["Εύκολη", "Μέτρια", "Δύσκολη"]


DIFF_C = {"Εύκολη": "#4CAF50", "Μέτρια": "#FF9800", "Δύσκολη": "#F44336"}
CAT_C  = {"Ψάρια":"#5B9BD5","Ζυμαρικά":"#E8A838","Κρέας":"#C0392B",
           "Φούρνος":"#8E44AD","Air Fryer":"#16A085","Vegan":"#27AE60"}

DARK    = "#232828"
DARK_H  = "#3a3f3f"
CAT_BG  = "#CECFCF"
DEL_C   = "#C0392B"
GRAY_C  = "#6c757d"

RECIPES: list[dict] = []
_ing_vars: list = []

#Προσθήκη RecipeManager για διαχείριση συνταγών με αυτόματη αποθήκευση
manager = RecipeManager(auto_seed  =True)

#Αυτή ειναι η μετάβαση μεταξύ UI(dicts) και Model (objects) 

def recipe_to_dict(recipe) -> dict:
    """Μετατρέπει Recipe object σε dict που περιμένει το UI."""
    return {
        "id": recipe.recipe_id,
        "name": recipe.title,
        "category": recipe.category,
        "difficulty": recipe.difficulty,
        "time_minutes": recipe.total_duration,
        "servings": recipe.servings,
        "image_path": None,
        "ingredients": [
            {"name": ing.name, "amount": ing.amount}
            for ing in recipe.ingredients
        ],
        "steps": [
            {
                "title": step.title,
                "description": step.instruction,
                "duration_minutes": step.get_duration_minutes(),
                "ingredients": [
                    f"{ing.amount} {ing.name}".strip() if ing.amount else ing.name
                    for ing in step.ingredients
                ]
            }
            for step in recipe.steps
        ]
    }

def refresh_recipes():
    """Φορτώνει όλες τις συνταγές από τη βάση στο RECIPES."""
    global RECIPES
    recipes = manager.get_all_recipes() # παιρνει τα objects απο το  model
    RECIPES = [recipe_to_dict(r) for r in recipes] #μετατρέπει σε dict για το UI

#διόρθωση format χρόνου σε ώρες και λεπτά 
def fmt(m: int) -> str:
    if m is None: return "_"
    try:
        m = int(m)
    except (ValueError, TypeError):
        return str(m)
    h, r = divmod(m, 60)
    return f"{h}ω {r}'" if h and r else f"{h}ω" if h else f"{m}'"


def placeholder(recipe: dict, size=(110, 82)) -> ctk.CTkImage:
    path = recipe.get("image_path")
    if path and os.path.exists(path):
        img = Image.open(path).convert("RGB")
        img.thumbnail(size, Image.LANCZOS)
        bg = Image.new("RGB", size, (240, 235, 230))
        bg.paste(img, ((size[0]-img.width)//2, (size[1]-img.height)//2))
        return ctk.CTkImage(light_image=bg, dark_image=bg, size=size)
    color = CAT_C.get(recipe.get("category",""), "#D9C9B0")
    img = Image.new("RGB", size, color)
    d = ImageDraw.Draw(img); cx, cy = size[0]//2, size[1]//2
    d.ellipse([cx-18,cy-18,cx+18,cy+18], fill="white")
    d.ellipse([cx-10,cy-10,cx+10,cy+10], fill=color)
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


app = ctk.CTk()
app.title("Συνταγες")
app.geometry("1280x800")

def show(f): f.tkraise()

def lbl(p, t="", **kw): return ctk.CTkLabel(p, text=t, **kw)
def btn(p, t, cmd=None, fg=DARK, hov=DARK_H, tc="white", **kw):
    return ctk.CTkButton(p, text=t, command=cmd, fg_color=fg, hover_color=hov, text_color=tc, **kw)
def div(p, **kw): return ctk.CTkFrame(p, height=1, fg_color="gray80", **kw)
def frm(p, **kw): return ctk.CTkFrame(p, fg_color="transparent", **kw)

home = ctk.CTkFrame(app, fg_color="#FFFFFF"); home.place(relwidth=1, relheight=1)

nav_bar = ctk.CTkFrame(home, fg_color=DARK, corner_radius=0, height=48)
nav_bar.pack(fill="x"); nav_bar.pack_propagate(False)

_nav_cmds = {}

#v6 SOS ΑΛΛΑΓΗ : Αφαίρεση "Ακολούθηση Συνταγής", διόρθωση ονόματος
# --------------------------------------------------------------
for label in ["Αναζήτηση Συνταγών", "Προσθηκη Συνταγης"]:
    btn(nav_bar, label, width=160, height=36, font=("Helvetica",12),
        fg=DARK, hov=DARK_H, corner_radius=0,
        cmd=lambda l=label: _nav_cmds[l]()
        ).pack(side="left", padx=2, pady=6)

lbl(home, "Κατηγοριες", font=("Helvetica",18,"bold")).pack(pady=(24,8))

cats_outer = ctk.CTkFrame(home, fg_color=CAT_BG, corner_radius=10)
cats_outer.pack(padx=60, pady=(0,30))

def render_home_categories():
    for w in cats_outer.winfo_children(): w.destroy()
    dynamic_categories = manager.get_categories()
    for idx, cat in enumerate(dynamic_categories):
        btn(cats_outer, cat, width=180, height=180, font=("Helvetica",15,"bold"),
            fg=DARK, hov=DARK_H, corner_radius=8, cmd=lambda c=cat: open_list(c)
            ).grid(row=idx//2, column=idx%2, padx=16, pady=16)

render_home_categories()


list_page = ctk.CTkFrame(app, fg_color="#FFFFFF"); list_page.place(relwidth=1, relheight=1)

lbar = frm(list_page); lbar.pack(fill="x", padx=24, pady=(14,8))
btn(lbar,"Αρχικη",width=90,height=30,fg="transparent",hov="gray90",tc="gray50",cmd=lambda: show(home)).pack(side="left")
list_title = lbl(lbar, "Συνταγες", font=("Helvetica",20,"bold"))
list_title.pack(side="left", padx=14)
btn(lbar,"+ Προσθηκη",width=110,height=30,cmd=lambda: open_add()).pack(side="right")


# v6 SOS ΑΛΛΑΓΗ : Προσθήκη μπάρας αναζήτησης
# --------------------------------------------------
search_bar = frm(list_page)
search_bar.pack(fill="x", padx=24, pady=(0,8))

search_entry = ctk.CTkEntry(search_bar, width=300, placeholder_text="Αναζητηση συνταγης...")
search_entry.pack(side="left", padx=(0,8))

search_btn = btn(search_bar, "Αναζητηση", width=100, height=28, 
                 cmd=lambda: perform_search())
search_btn.pack(side="left", padx=(0,8))

clear_btn = btn(search_bar, "Καθαρισμος", width=100, height=28, fg=GRAY_C, hov="#5a6268",
                cmd=lambda: clear_search())
clear_btn.pack(side="left")

def perform_search():
    """Εκτελεί αναζήτηση με βάση το κείμενο της μπάρας."""
    term = search_entry.get().strip()
    if term:
        # Χρησιμοποιούμε το manager για αναζήτηση
        results = manager.search_recipes(term)
        global RECIPES
        RECIPES = [recipe_to_dict(r) for r in results]
        list_title.configure(text=f"Αποτελεσματα: '{term}'")
    else:
        refresh_recipes()
        list_title.configure(text="Συνταγες")
    render_list()

def clear_search():
    """Καθαρίζει την αναζήτηση και εμφανίζει όλες τις συνταγές."""
    search_entry.delete(0, "end")
    refresh_recipes()
    list_title.configure(text="Συνταγες")
    render_list()

div(list_page).pack(fill="x", padx=24, pady=(0,6))
list_scroll = ctk.CTkScrollableFrame(list_page, fg_color="transparent")
list_scroll.pack(fill="both", expand=True, padx=24, pady=(0,14))

_cur_filter = ["Ολες"]

def open_list(cat="Ολες"):
    _cur_filter[0] = cat
    list_title.configure(text="Συνταγες" if cat=="Ολες" else cat)
    refresh_recipes() # Φορτώνει τις συνταγές από τη βάση δεδομένων 
    render_list(); show(list_page)

def render_list():
    for w in list_scroll.winfo_children(): w.destroy()
    data = RECIPES if _cur_filter[0]=="Ολες" else [r for r in RECIPES if r["category"]==_cur_filter[0]]
    if not data:
        lbl(list_scroll,"Δεν υπαρχουν συνταγες.",font=("Helvetica",14),text_color="gray60").pack(pady=50)
        return
    for r in data: list_card(r)

def list_card(r):
    card = ctk.CTkFrame(list_scroll, corner_radius=10, fg_color="white",
                        border_width=1, border_color="gray88")
    card.pack(fill="x", pady=4)
    lbl(card, image=placeholder(r)).pack(side="left", padx=(12,8), pady=10)

    info = frm(card); info.pack(side="left", fill="both", expand=True, pady=10)
    lbl(info, r["name"], font=("Helvetica",15,"bold"), anchor="w").pack(anchor="w")

    badges = frm(info); badges.pack(anchor="w", pady=(4,0))
    for t, bg in [(r["category"],CAT_C.get(r["category"],"#888")),
                  (r["difficulty"],DIFF_C.get(r["difficulty"],"#888"))]:
        lbl(badges, t, fg_color=bg, corner_radius=7, text_color="white",
            font=("Helvetica",11), padx=8, pady=2).pack(side="left", padx=(0,5))

    stats = frm(info); stats.pack(anchor="w", pady=(5,0))
    lbl(stats, fmt(r["time_minutes"]), font=("Helvetica",12), text_color="gray55").pack(side="left", padx=(0,14))
    lbl(stats, f"{r['servings']} μεριδες", font=("Helvetica",12), text_color="gray55").pack(side="left")

    bx = frm(card); bx.pack(side="right", padx=14, pady=10)
    btn(bx,"Ανοιγμα",width=96,height=28,cmd=lambda r=r: open_recipe(r)).pack(pady=(0,4))
    btn(bx,"Επεξεργασια",width=96,height=28,fg=GRAY_C,hov="#5a6268",cmd=lambda r=r: open_edit(r)).pack(pady=(0,4))
    btn(bx,"Διαγραφη",width=96,height=28,fg=DEL_C,hov="#A93226",cmd=lambda r=r: confirm_delete(r)).pack()

def confirm_delete(r):
    d = ctk.CTkToplevel(app); d.title("Διαγραφη"); d.geometry("340x140"); d.grab_set()
    lbl(d,f"Διαγραφη «{r['name']}»;\nΔεν αναιρειται.",font=("Helvetica",13),justify="center").pack(pady=(22,12))
    row = frm(d); row.pack()
    btn(row,"Ακυρωση",width=96,fg=GRAY_C,hov="#5a6268",cmd=d.destroy).pack(side="left",padx=7)
    def do_delete():
        old_categories = manager.get_categories()
        manager.delete_recipe(r["id"]) # Διαγραφή από τη βάση δεδομένων
        refresh_recipes()
        if set(manager.get_categories()) != set(old_categories):
            render_home_categories()
        render_list() # Ενημέρωση της λίστας
        d.destroy()
    btn(row,"Διαγραφη",width=96,fg=DEL_C,hov="#A93226",
        cmd=do_delete).pack(side="left",padx=7)


detail_page = ctk.CTkFrame(app, fg_color="#FFFFFF"); detail_page.place(relwidth=1, relheight=1)

dnav = ctk.CTkFrame(detail_page, fg_color="transparent", height=48)
dnav.pack(fill="x", padx=18, pady=(10,0)); dnav.pack_propagate(False)
btn(dnav,"Λιστα",width=80,height=30,fg="transparent",hov="gray90",tc="gray50",cmd=lambda: show(list_page)).pack(side="left",pady=9)
d_exec_btn = btn(dnav,"Εκτελεση",width=110,height=30)
d_exec_btn.pack(side="right",pady=9)
d_edit_btn = btn(dnav,"Επεξεργασια",width=110,height=30,fg=GRAY_C,hov="#5a6268")
d_edit_btn.pack(side="right",padx=(0,8),pady=9)

detail_scroll = ctk.CTkScrollableFrame(detail_page, fg_color="transparent")
detail_scroll.pack(fill="both", expand=True, padx=18, pady=(0,10))

def open_recipe(r):
    _ing_vars.clear()
    for w in detail_scroll.winfo_children(): w.destroy()
    d_edit_btn.configure(command=lambda: open_edit(r))
    d_exec_btn.configure(command=lambda: open_exec(r))

    hdr = ctk.CTkFrame(detail_scroll, fg_color="gray95", corner_radius=10)
    hdr.pack(fill="x", pady=(0,14))
    lbl(hdr, image=placeholder(r,(190,142))).pack(side="left",padx=18,pady=14)
    meta = frm(hdr); meta.pack(side="left",fill="both",expand=True,pady=14,padx=(0,18))
    lbl(meta, r["name"], font=("Helvetica",22,"bold"), anchor="w").pack(anchor="w")

    bdg = frm(meta); bdg.pack(anchor="w",pady=(7,0))
    for t, bg in [(r["category"],CAT_C.get(r["category"],"#888")),
                  (r["difficulty"],DIFF_C.get(r["difficulty"],"#888"))]:
        lbl(bdg,t,fg_color=bg,corner_radius=7,text_color="white",font=("Helvetica",11),padx=8,pady=2
            ).pack(side="left",padx=(0,6))

    sr = frm(meta); sr.pack(anchor="w",pady=(8,0))
    lbl(sr,fmt(r["time_minutes"]),font=("Helvetica",12),text_color="gray55").pack(side="left",padx=(0,18))
    lbl(sr,f"{r['servings']} μεριδες",font=("Helvetica",12),text_color="gray55").pack(side="left")

    body = frm(detail_scroll); body.pack(fill="both",expand=True)
    body.columnconfigure(0,weight=1,minsize=230); body.columnconfigure(1,weight=2)

    ing_panel = ctk.CTkFrame(body, corner_radius=10); ing_panel.grid(row=0,column=0,sticky="nsew",padx=(0,10))
    lbl(ing_panel,"Υλικα",font=("Helvetica",14,"bold")).pack(pady=(12,4),padx=14,anchor="w")
    div(ing_panel).pack(fill="x",padx=14,pady=(0,7))
    for ing in r["ingredients"]:
        var = ctk.BooleanVar()
        row = frm(ing_panel); row.pack(fill="x",padx=8,pady=2)
        ctk.CTkCheckBox(row,text="",variable=var,width=22,
            fg_color=DARK, hover_color=DARK_H, checkmark_color="white",
            command=lambda v=var,rw=row: [w.configure(text_color="gray70" if v.get() else "gray10")
                                          for w in rw.winfo_children() if isinstance(w,ctk.CTkLabel)]
            ).pack(side="left")
        lbl(row,ing["name"],font=("Helvetica",12),anchor="w").pack(side="left",expand=True,fill="x")
        lbl(row,ing["amount"],font=("Helvetica",11,"bold"),text_color="gray55").pack(side="right",padx=(4,8))
        _ing_vars.append((var, row))
    btn(ing_panel,"Καθαρισμος",height=26,width=100,fg="transparent",hov="gray90",tc="gray50",
        font=("Helvetica",11),
        cmd=lambda: [v.set(False) or [w.configure(text_color="gray10")
                     for w in rw.winfo_children() if isinstance(w,ctk.CTkLabel)]
                     for v,rw in _ing_vars]).pack(pady=(8,12))

    sp = ctk.CTkFrame(body, corner_radius=10); sp.grid(row=0,column=1,sticky="nsew")
    lbl(sp,"Βηματα",font=("Helvetica",14,"bold")).pack(pady=(12,4),padx=14,anchor="w")
    div(sp).pack(fill="x",padx=14,pady=(0,7))
    for i, s in enumerate(r["steps"],1):
        c = ctk.CTkFrame(sp,fg_color="gray96",corner_radius=8); c.pack(fill="x",padx=10,pady=4)
        top = frm(c); top.pack(fill="x",padx=10,pady=(9,4))
        lbl(top,str(i),font=("Helvetica",12,"bold"),width=24,height=24,
            fg_color="gray30",text_color="white",corner_radius=12).pack(side="left")
        lbl(top,f"  {s['title']}",font=("Helvetica",13,"bold"),anchor="w").pack(side="left",fill="x",expand=True)
        if s.get("duration_minutes"):
            lbl(top,fmt(s["duration_minutes"]),font=("Helvetica",11,"bold"),text_color="#E8A838").pack(side="right")
        lbl(c,s["description"],font=("Helvetica",12),wraplength=500,justify="left",anchor="w"
            ).pack(fill="x",padx=10,pady=(2,6))
        if s.get("ingredients"):
            ib = ctk.CTkFrame(c,fg_color="gray90",corner_radius=6); ib.pack(fill="x",padx=10,pady=(0,9))
            lbl(ib," · ".join(s["ingredients"]),font=("Helvetica",11),text_color="#5B9BD5",
                anchor="w",wraplength=500).pack(padx=9,pady=4,anchor="w")
    lbl(sp,"").pack(pady=4)
    show(detail_page)


exec_page = ctk.CTkFrame(app, fg_color="#FFFFFF"); exec_page.place(relwidth=1, relheight=1)

enav = ctk.CTkFrame(exec_page,fg_color="transparent",height=46)
enav.pack(fill="x",padx=18,pady=(10,0)); enav.pack_propagate(False)
btn(enav,"Συνταγη",width=80,height=30,fg="transparent",hov="gray90",tc="gray50",cmd=lambda: show(detail_page)).pack(side="left",pady=8)
e_title  = lbl(enav,"",font=("Helvetica",17,"bold")); e_title.pack(side="left",padx=12)
e_count  = lbl(enav,"",font=("Helvetica",12),text_color="gray55"); e_count.pack(side="right",padx=12)

e_prog = ctk.CTkProgressBar(exec_page,height=8,corner_radius=4,progress_color=DARK)
e_prog.pack(fill="x",padx=18,pady=(4,10)); e_prog.set(0)

e_card = ctk.CTkFrame(exec_page,corner_radius=12,fg_color="gray96")
e_card.pack(fill="both",expand=True,padx=18,pady=(0,10))

e_num   = lbl(e_card,"",font=("Helvetica",11),text_color="gray55"); e_num.pack(pady=(22,3))
e_stitle= lbl(e_card,"",font=("Helvetica",21,"bold")); e_stitle.pack(pady=(0,5))
e_dur   = lbl(e_card,"",font=("Helvetica",12,"bold"),text_color="#E8A838"); e_dur.pack(pady=(0,14))
div(e_card).pack(fill="x",padx=50,pady=(0,14))
e_desc  = lbl(e_card,"",font=("Helvetica",13),wraplength=680,justify="center"); e_desc.pack(padx=40,pady=(0,18))
e_ib    = ctk.CTkFrame(e_card,fg_color="gray88",corner_radius=8)
e_ib.pack(padx=50,pady=(0,18),fill="x")
e_ilbl  = lbl(e_ib,"",font=("Helvetica",12),text_color="#5B9BD5",wraplength=660,justify="center")
e_ilbl.pack(padx=12,pady=8)

eb_row = frm(exec_page); eb_row.pack(pady=(0,14))
e_prev = btn(eb_row,"Προηγουμενο",width=150,height=36,fg=GRAY_C,hov="#5a6268")
e_prev.pack(side="left",padx=8)
e_next = btn(eb_row,"Επομενο",width=150,height=36)
e_next.pack(side="left",padx=8)

_es = {"r":None,"i":0}

def _erender():
    r=_es["r"]; i=_es["i"]; steps=r["steps"]; total=len(steps)
    if total == 0:
        e_title.configure(text=r["name"])
        e_count.configure(text="0 / 0")
        e_prog.set(0)
        e_num.configure(text="ΔΕΝ ΥΠΑΡΧΟΥΝ ΒΗΜΑΤΑ")
        e_stitle.configure(text="")
        e_dur.configure(text="")
        e_desc.configure(text="Αυτή η συνταγή δεν έχει βήματα εκτέλεσης.")
        e_ib.pack_forget()
        e_prev.configure(state="disabled")
        e_next.configure(text="Τελος", command=lambda: show(detail_page))
        return

    s=steps[i]
    e_title.configure(text=r["name"]); e_count.configure(text=f"{i+1} / {total}")
    e_prog.set((i+1)/total); e_num.configure(text=f"ΒΗΜΑ {i+1}")
    e_stitle.configure(text=s["title"])
    e_dur.configure(text=fmt(s["duration_minutes"]) if s.get("duration_minutes") else "")
    e_desc.configure(text=s["description"])
    ings = s.get("ingredients",[])
    if ings: e_ilbl.configure(text=" · ".join(ings)); e_ib.pack(padx=50,pady=(0,18),fill="x")
    else: e_ib.pack_forget()
    e_prev.configure(state="normal" if i>0 else "disabled", command=lambda:(_es.update(i=_es["i"]-1),_erender()))
    last = i>=total-1
    e_next.configure(text="Τελος" if last else "Επομενο",
                     command=(lambda:show(detail_page)) if last else (lambda:(_es.update(i=_es["i"]+1),_erender())))

def open_exec(r):
    _es["r"]=r; _es["i"]=0; _erender(); show(exec_page)


add_page = ctk.CTkFrame(app, fg_color="#FFFFFF"); add_page.place(relwidth=1, relheight=1)

anav = ctk.CTkFrame(add_page,fg_color="transparent",height=46)
anav.pack(fill="x",padx=18,pady=(10,0)); anav.pack_propagate(False)
btn(anav,"Πισω",width=80,height=30,fg="transparent",hov="gray90",tc="gray50",cmd=lambda: show(home)).pack(side="left",pady=8)
a_title = lbl(anav,"Νεα Συνταγη",font=("Helvetica",18,"bold")); a_title.pack(side="left",padx=12)
a_del_btn = btn(anav,"Διαγραφη",width=100,height=30,fg=DEL_C,hov="#A93226")

add_scroll = ctk.CTkScrollableFrame(add_page, fg_color="transparent")
add_scroll.pack(fill="both", expand=True, padx=28, pady=(0,10))

_er=[None]; _airows=[]; _asrows=[]; _aw={}

def wlbl(p, t, **kw): return lbl(p, t, text_color="white", **kw)

def _form(parent, w, ir, sr, on_save, recipe=None):
    B = ctk.CTkFrame(parent, corner_radius=10, fg_color=DARK); B.pack(fill="x", pady=(0,10))
    wlbl(B,"Βασικα Στοιχεια",font=("Helvetica",13,"bold")).grid(row=0,column=0,columnspan=4,padx=14,pady=(10,4),sticky="w")

    fields = [("Ονομα *",1,0,1,3,"name",270,recipe.get("name","") if recipe else "","π.χ. Μουσακας","entry"),
              ("Κατηγορια *",2,0,1,1,"cat",148,recipe.get("category",CATEGORIES[0]) if recipe else CATEGORIES[0],CATEGORIES,"menu"),
              ("Δυσκολια *",2,2,1,1,"diff",128,recipe.get("difficulty",DIFFICULTIES[0]) if recipe else DIFFICULTIES[0],DIFFICULTIES,"menu"),
              ("Χρονος (λεπτα) *",3,0,1,1,"time",86,str(recipe["time_minutes"]) if recipe else "","45","entry"),
              ("Μεριδες *",3,2,1,1,"serv",68,str(recipe["servings"]) if recipe else "","4","entry")]

    for label, row, col, rs, cs, key, width, val, extra, kind in fields:
        wlbl(B, label).grid(row=row, column=col, padx=14, pady=3, sticky="w")
        if kind == "entry":
            e = ctk.CTkEntry(B, width=width, placeholder_text=extra)
            e.grid(row=row, column=col+1, columnspan=cs, padx=7, pady=3 if row<3 else (3,12), sticky="w")
            if val: e.insert(0, val)
            w[key] = e
        else:
            v = ctk.StringVar(value=val)
            ctk.CTkOptionMenu(B, variable=v, values=extra, width=width).grid(row=row, column=col+1, padx=7, pady=3, sticky="w")
            w[key] = v

    I = ctk.CTkFrame(parent, corner_radius=10, fg_color=DARK); I.pack(fill="x", pady=(0,10))
    wlbl(I,"Υλικα",font=("Helvetica",13,"bold")).pack(anchor="w",padx=14,pady=(10,4))
    ilf = frm(I); ilf.pack(fill="x", padx=14)

    def ai(nv="", av=""):
        rf = frm(ilf); rf.pack(fill="x", pady=2)
        n = ctk.CTkEntry(rf,width=210,placeholder_text="Υλικο"); n.pack(side="left",padx=(0,5))
        if nv: n.insert(0,nv)
        a = ctk.CTkEntry(rf,width=96,placeholder_text="Ποσοτητα"); a.pack(side="left",padx=(0,5))
        if av: a.insert(0,av)
        btn(rf,"x",width=26,height=26,fg=DEL_C,hov="#A93226",
            cmd=lambda:(ir.remove(next(t for t in ir if t[2] is rf)),rf.destroy())).pack(side="left")
        ir.append((n,a,rf))

    for i in (recipe["ingredients"] if recipe else []):
        ai(i.get("name",""),i.get("amount",""))
    btn(I,"+ Υλικο",width=86,height=24,fg=DARK,hov=DARK_H,cmd=ai).pack(anchor="w",padx=14,pady=(5,10))

    S = ctk.CTkFrame(parent, corner_radius=10, fg_color=DARK); S.pack(fill="x", pady=(0,10))
    wlbl(S,"Βηματα",font=("Helvetica",13,"bold")).pack(anchor="w",padx=14,pady=(10,4))
    slf = frm(S); slf.pack(fill="x", padx=14)
    sn = [0]

    def aS(t="", desc="", dur="", ings=""):
        sn[0] += 1
        sf = ctk.CTkFrame(slf, fg_color="#3a3f3f", corner_radius=8); sf.pack(fill="x", pady=3)
        hr = frm(sf); hr.pack(fill="x", padx=8, pady=(7,3))
        wlbl(hr,f"Βημα {sn[0]}",font=("Helvetica",11,"bold")).pack(side="left")
        btn(hr,"x",width=24,height=22,fg=DEL_C,hov="#A93226",
            cmd=lambda:(sr.remove(next(x for x in sr if x[4] is sf)),sf.destroy())).pack(side="right")
        te2 = ctk.CTkEntry(sf,width=380,placeholder_text="Τιτλος"); te2.pack(anchor="w",padx=8,pady=(0,3))
        if t: te2.insert(0,t)
        de = ctk.CTkTextbox(sf,width=460,height=50,fg_color="#2e3333",text_color="white"); de.pack(anchor="w",padx=8,pady=(0,3))
        if desc: de.insert("1.0",desc)
        dr = frm(sf); dr.pack(fill="x", padx=8, pady=(0,8))
        wlbl(dr,"Διαρκεια:").pack(side="left")
        du = ctk.CTkEntry(dr,width=56,placeholder_text="0"); du.pack(side="left",padx=4)
        if dur: du.insert(0,str(dur))
        wlbl(dr,"  Υλικα:").pack(side="left",padx=(10,0))
        ie = ctk.CTkEntry(dr,width=240,placeholder_text="Αυγα, Αλευρι"); ie.pack(side="left",padx=4)
        if ings: ie.insert(0,ings)
        sr.append((te2,de,du,ie,sf))

    for s in (recipe["steps"] if recipe else []):
        aS(s.get("title",""),s.get("description",""),s.get("duration_minutes",""),", ".join(s.get("ingredients",[])))
    btn(S,"+ Βημα",width=86,height=24,fg=DARK,hov=DARK_H,cmd=aS).pack(anchor="w",padx=14,pady=(4,10))

    btn(parent,"Αποθηκευση",height=36,font=("Helvetica",12,"bold"),fg=DARK,hov=DARK_H,cmd=on_save).pack(pady=(4,18))


def _collect():
    try:
        name = _aw["name"].get().strip()
    except Exception:
        return None
    if not name: return None
    try: tm=int(_aw["time"].get()); sv=int(_aw["serv"].get())
    except ValueError: return None
    ings=[{"name":n.get().strip(),"amount":a.get().strip()} for n,a,_ in _airows if n.get().strip()]
    steps=[]
    for te,de,du,ie,_ in _asrows:
        t=te.get().strip()
        if not t: continue
        try: d=int(du.get().strip() or "0")
        except ValueError: d=0
        steps.append({"title":t,"description":de.get("1.0","end").strip(),"duration_minutes":d,
                       "ingredients":[x.strip() for x in ie.get().split(",") if x.strip()]})
    return {"name":name,"category":_aw["cat"].get(),"difficulty":_aw["diff"].get(),
            "time_minutes":tm,"servings":sv,"image_path":None,"ingredients":ings,"steps":steps}


def _save():
    data = _collect()
    if not data: return
    old_categories = manager.get_categories()
    r = _er[0]

    # Μετατροπή UI format σε Model format
    ingredients_list = [{"name": ing["name"], "amount": ing["amount"]}
                       for ing in data.get("ingredients", [])]
    steps_list = []
    for idx, s in enumerate(data.get("steps", []), 1):
        steps_list.append({
            "step_number": idx,
            "title": s["title"],
            "instruction": s["description"],
            "time_hours": "",
            "time_minutes": str(s.get("duration_minutes", "")),
            "ingredients": [{"name": ing, "amount": ""} for ing in s.get("ingredients", [])]
        })

    if r:
        # Ενημέρωση υπάρχουσας συνταγής (πλήρης ενημέρωση)
        success, error = manager.update_full_recipe(
            r["id"], data["name"], data["category"],
            data["difficulty"], data["time_minutes"], data["servings"],
            ingredients_list, steps_list
        )
        if not success:
            print(f"Σφάλμα κατά την ενημέρωση: {error}")
            return

    else:
        # Δημιουργία νέας
        recipe, error = manager.create_recipe(
            title=data["name"],
            category=data["category"],
            difficulty=data["difficulty"],
            total_duration=data["time_minutes"],
            servings=data["servings"],
            ingredients_list=ingredients_list,
            steps_list=steps_list
        )
        if error:
            print(f"Σφάλμα: {error}")
            return

    _er[0] = None
    refresh_recipes()

    # Αν προστέθηκε νέα κατηγορία, ανανέωση της αρχικής οθόνης
    if set(manager.get_categories()) != set(old_categories):
        render_home_categories()

    render_list()
    show(list_page)


def _rebuild(recipe=None):
    for w in add_scroll.winfo_children(): w.destroy()
    _airows.clear(); _asrows.clear(); _aw.clear()
    _form(add_scroll,_aw,_airows,_asrows,_save,recipe)

def open_add():
    _er[0]=None; a_title.configure(text="Νεα Συνταγη"); a_del_btn.pack_forget()
    _rebuild(); show(add_page)

def open_edit(r):
    _er[0]=r; a_title.configure(text="Επεξεργασια")
    def do_delete():
        old_categories = manager.get_categories()
        manager.delete_recipe(r["id"])
        refresh_recipes()

        if set(manager.get_categories()) != set(old_categories):
            render_home_categories()

        render_list()
        show(list_page)
        a_del_btn.pack_forget()
    a_del_btn.configure(command=do_delete)
    a_del_btn.pack(side="right",pady=8)
    _rebuild(r); show(add_page)

_rebuild()


#v6 SOS ΑΛΛΑΓΗ 3: Αφαίρεση "Ακολούθηση", διόρθωση ονόματος
# ---------------------------------------------------------------
_nav_cmds["Αναζήτηση Συνταγών"] = lambda: open_list()
_nav_cmds["Προσθηκη Συνταγης"]   = lambda: open_add()

show(home)
app.mainloop()
