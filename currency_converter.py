import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime
import os

class CurrencyConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Конвертер валют ЦБ РФ")
        self.root.geometry("600x500")
        
        self.api_url = "https://www.cbr-xml-daily.ru/daily_json.js"
        self.history_file = "history.json"
        self.rates_data = {}
        self.history = self.load_history()
        
        self.setup_ui()
        self.load_rates()
    
    def load_rates(self):
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                self.rates_data = response.json()
                self.rates_data['Valute']['RUB'] = {
                    'CharCode': 'RUB', 'Name': 'Российский рубль',
                    'Nominal': 1, 'Value': 1
                }
                self.status.set(f"Курсы загружены ({self.rates_data.get('Date', '')})")
                self.update_currency_list()
            else:
                self.status.set(f"Ошибка API: {response.status_code}")
        except:
            self.status.set("Нет соединения. Демо-режим")
            self.rates_data = {
                'Valute': {
                    'RUB': {'CharCode': 'RUB', 'Name': 'Российский рубль', 'Nominal': 1, 'Value': 1},
                    'USD': {'CharCode': 'USD', 'Name': 'Доллар США', 'Nominal': 1, 'Value': 92.5},
                    'EUR': {'CharCode': 'EUR', 'Name': 'Евро', 'Nominal': 1, 'Value': 100.8}
                }
            }
            self.update_currency_list()
    
    def update_currency_list(self):
        codes = [f"{v['CharCode']} - {v['Name']}" for v in self.rates_data['Valute'].values()]
        self.from_combo['values'] = codes
        self.to_combo['values'] = codes
        if codes:
            self.from_var.set(codes[1] if len(codes) > 1 else codes[0])
            self.to_var.set(codes[0])
    
    def setup_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)
        
        # Поле суммы
        ttk.Label(main, text="Сумма:").pack()
        self.amount_var = tk.StringVar(value="1")
        ttk.Entry(main, textvariable=self.amount_var, font=("Arial", 12), width=25).pack(pady=5)
        
        # Выбор валют
        ttk.Label(main, text="Из валюты:").pack()
        self.from_var = tk.StringVar()
        self.from_combo = ttk.Combobox(main, textvariable=self.from_var, state="readonly", width=35)
        self.from_combo.pack()
        
        ttk.Button(main, text="<-->", width=5, command=self.swap).pack(pady=5)
        
        ttk.Label(main, text="В валюту:").pack()
        self.to_var = tk.StringVar()
        self.to_combo = ttk.Combobox(main, textvariable=self.to_var, state="readonly", width=35)
        self.to_combo.pack()
        
        # Кнопка конвертации
        ttk.Button(main, text="Конвертировать", command=self.convert).pack(pady=10)
        
        # Результат
        self.result_var = tk.StringVar()
        ttk.Label(main, textvariable=self.result_var, font=("Arial", 14, "bold"), foreground="blue").pack()
        self.rate_var = tk.StringVar()
        ttk.Label(main, textvariable=self.rate_var, font=("Arial", 9), foreground="gray").pack()
        
        # Статус
        self.status = tk.StringVar(value="Загрузка...")
        ttk.Label(main, textvariable=self.status, font=("Arial", 8)).pack(pady=5)
        
        # История
        hist_frame = ttk.LabelFrame(main, text="История", padding=5)
        hist_frame.pack(fill="both", expand=True, pady=10)
        
        btns = ttk.Frame(hist_frame)
        btns.pack(fill="x")
        ttk.Button(btns, text="Очистить", command=self.clear_history).pack(side="left")
        ttk.Button(btns, text="Экспорт JSON", command=self.export).pack(side="left", padx=5)
        
        self.tree = ttk.Treeview(hist_frame, columns=("date", "from", "to", "amount", "result"), show="headings", height=8)
        self.tree.heading("date", text="Дата"); self.tree.column("date", width=120)
        self.tree.heading("from", text="Из"); self.tree.column("from", width=50)
        self.tree.heading("to", text="В"); self.tree.column("to", width=50)
        self.tree.heading("amount", text="Сумма"); self.tree.column("amount", width=80)
        self.tree.heading("result", text="Результат"); self.tree.column("result", width=80)
        self.tree.pack(fill="both", expand=True)
        
        self.update_tree()
    
    def swap(self):
        f, t = self.from_var.get(), self.to_var.get()
        self.from_var.set(t); self.to_var.set(f)
    
    def get_code(self, s):
        return s.split(" - ")[0]
    
    def convert(self):
        try:
            amount = float(self.amount_var.get().replace(',', '.'))
            if amount <= 0: raise ValueError("Сумма должна быть положительной")
            
            f_code = self.get_code(self.from_var.get())
            t_code = self.get_code(self.to_var.get())
            
            if f_code == t_code:
                self.result_var.set(f"{amount:.2f} {f_code} = {amount:.2f} {t_code}")
                return
            
            f_data = self.rates_data['Valute'][f_code]
            t_data = self.rates_data['Valute'][t_code]
            
            rub = (amount / f_data['Nominal']) * f_data['Value']
            result = (rub * t_data['Nominal']) / t_data['Value']
            
            self.result_var.set(f"{amount:.2f} {f_code} = {result:.2f} {t_code}")
            rate = (t_data['Value']/t_data['Nominal']) / (f_data['Value']/f_data['Nominal'])
            self.rate_var.set(f"Курс: 1 {f_code} = {rate:.4f} {t_code}")
            
            self.history.append({
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "from": f_code, "to": t_code,
                "amount": amount, "result": round(result, 2)
            })
            if len(self.history) > 50: self.history = self.history[-50:]
            self.save_history()
            self.update_tree()
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except KeyError:
            messagebox.showerror("Ошибка", "Валюта не найдена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
    
    def load_history(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    
    def save_history(self):
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def update_tree(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for h in reversed(self.history):
            self.tree.insert("", "end", values=(h["date"], h["from"], h["to"], f"{h['amount']:.2f}", f"{h['result']:.2f}"))
    
    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Очистить историю?"):
            self.history = []
            self.save_history()
            self.update_tree()
    
    def export(self):
        if not self.history:
            messagebox.showwarning("Пусто", "История пуста")
            return
        name = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(name, "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Готово", f"Сохранено: {name}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CurrencyConverter(root)
    root.mainloop()
