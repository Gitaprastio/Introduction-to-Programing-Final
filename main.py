import pandas as pd
import datetime

transaksi_df = pd.read_csv('transaksi.csv')
barang_df = pd.read_csv('barang.csv')

class FungsiDasar:
    def __init__(self, transaksi_df, barang_df):
        self._transaksi_df = transaksi_df
        self._barang_df = barang_df

    def _is_valid_id(self, id_barang):
        if id_barang not in self._barang_df['IdBarang'].values:
            raise ValueError('Invalid ID Barang')
        return True
    
    def get_nama_barang(self, id_barang):
        if self._is_valid_id(id_barang):
            return self._barang_df[self._barang_df['IdBarang'] == id_barang]['Nama Barang'].iloc[0]
        else:
            return "Invalid ID"

    def get_deskripsi_barang(self, id_barang):
        if self._is_valid_id(id_barang):
            return self._barang_df[self._barang_df['IdBarang'] == id_barang]['Deskripsi'].iloc[0]
        else:
            return "Invalid ID"

    def simpan_transaksi(self):
        try:
            self._transaksi_df.to_csv('transaksi.csv', index=False)
        except Exception as e:
            print("Gagal menyimpan Transaksi: ", str(e))

    def catat_transaksi(self, JenisTransaksi, IdBarang, Jumlah, Harga):
        if JenisTransaksi not in ['Beli', 'Jual']:
            print("JenisTransaksi harus 'Beli' atau 'Jual'")
            return
        
        try:
            if not self._is_valid_id(IdBarang):
                return
            Jumlah = int(Jumlah)
            Harga = int(Harga)
        except ValueError as ve:
            print(f"ID Barang Tidak Ditemukan: {ve}")
            return

        new_row = {'JenisTransaksi': JenisTransaksi, 'IdBarang': str(IdBarang), 'Jumlah': Jumlah, 'Harga': Harga}
        highest_id = self._transaksi_df['IdTransaksi'].max()
        new_row['IdTransaksi'] = highest_id + 1
        now = datetime.datetime.now()
        new_row['Tanggal'] = now.strftime('%Y-%m-%d')
        new_row['Jam'] = now.strftime('%H:%M:%S')

        self._transaksi_df.loc[len(self._transaksi_df)+1] = new_row

        self.simpan_transaksi()

class Analytics:
    @staticmethod
    def summary_per_IdBarang(transaksi_df): 
        transaksi_df['NilaiTransaksi'] = transaksi_df['Jumlah'] * transaksi_df['Harga']
        transaksi_beli_df = transaksi_df[transaksi_df['JenisTransaksi'] == 'Beli']
        ringkasan_beli_df = transaksi_beli_df.pivot_table(index='IdBarang', values=['NilaiTransaksi', 'Jumlah'], aggfunc='sum')
        ringkasan_beli_df = ringkasan_beli_df.rename(columns={'NilaiTransaksi': 'Pembelian - Total Beli (IDR)', 'Jumlah': 'Pembelian - Total Beli (Jumlah)'})
        ringkasan_beli_df['Pembelian - Harga Beli Per Unit Rata Rata'] = ringkasan_beli_df['Pembelian - Total Beli (IDR)'] / ringkasan_beli_df['Pembelian - Total Beli (Jumlah)']
        ringkasan_beli_df['Pembelian - Harga Beli Per Unit Rata Rata'] = ringkasan_beli_df['Pembelian - Harga Beli Per Unit Rata Rata'].round().astype(int)

        transaksi_jual_df = transaksi_df[transaksi_df['JenisTransaksi'] == 'Jual']
        ringkasan_jual_df = transaksi_jual_df.pivot_table(index='IdBarang', values=['NilaiTransaksi', 'Jumlah'], aggfunc='sum')
        ringkasan_jual_df = ringkasan_jual_df.rename(columns={'NilaiTransaksi': 'Penjualan - Total Jual (IDR)', 'Jumlah': 'Penjualan - Total Jual (Jumlah)'})

        ringkasan_df = pd.merge(ringkasan_beli_df, ringkasan_jual_df, on='IdBarang', how='outer')
        ringkasan_df['Penjualan - COGS'] = ringkasan_df['Penjualan - Total Jual (Jumlah)'] * ringkasan_df['Pembelian - Harga Beli Per Unit Rata Rata']
        ringkasan_df['Penjualan - COGS'] = ringkasan_df['Penjualan - COGS'].round().astype(int)
        ringkasan_df['Laba'] = ringkasan_df['Penjualan - Total Jual (IDR)'] - ringkasan_df['Penjualan - COGS']
        ringkasan_df['Stok - Jumlah Stok'] = ringkasan_df['Pembelian - Total Beli (Jumlah)'] - ringkasan_df['Penjualan - Total Jual (Jumlah)']
        ringkasan_df['Stok - Total Nilai Stok'] = ringkasan_df['Stok - Jumlah Stok'] * ringkasan_df['Pembelian - Harga Beli Per Unit Rata Rata']
        return ringkasan_df
    
class AppUI:
    def __init__(self):
        try:
            self.tampilan_df = pd.read_excel('tampilan.xlsx')
        except FileNotFoundError as e:
            print(f"File tidak ditemukan: {e}")
            self.tampilan_df = None

    def show_ui(self, address):
        try:
            text = self.tampilan_df[(self.tampilan_df['Method'] == 'Body') & (self.tampilan_df['Address'] == address)]['Text'].iloc[0]
            print(str(text))
        except IndexError:
            print(f"{address} tidak ditemukan. Cek file tampilan.xlsx.")

    def get_input(self, address):
        try:
            text = self.tampilan_df[(self.tampilan_df['Method'] == 'Input') & (self.tampilan_df['Address'] == address)]['Text'].iloc[0]
            user_input = input(str(text) + ": ")
            return user_input
        except IndexError:
            print(f"{address} tidak ditemukan. Cek file tampilan.xlsx.")


class AppQlontong(AppUI, FungsiDasar):  
    def __init__(self, transaksi_df, barang_df):
        super().__init__()  
        FungsiDasar.__init__(self, transaksi_df, barang_df)  

    def catat_penjualan(self): 
        self.show_ui('catat_penjualan')
        while True:
            idBarang = self.get_input('catat_penjualan_IdBarang')
            if self._is_valid_id(idBarang):
                break
            else:
                print("ID Barang tidak valid. Silakan coba lagi.")
                    
        namaBarang = self.get_nama_barang(idBarang)
        print(f"Nama Barang: {namaBarang}, Apakah benar? (y/n)")
        while True:
            confirm = self.get_input('catat_penjualan_Confirm_id')  
            if confirm.lower() == 'y':
                break
            elif confirm.lower() == 'n':
                self.catat_penjualan()  
            else:
                print("Input tidak valid. Silakan coba lagi.")
    
                    
        jumlah = self.get_input('catat_penjualan_Jumlah')  
        harga = self.get_input('catat_penjualan_Harga')  
        self.catat_transaksi('Jual', idBarang, jumlah, harga)  
        print(f'Penjualan barang dengan ID {idBarang} sebanyak {jumlah} dengan harga {harga} berhasil dicatat.')

    

    def main_page(self): 
        AppUI().show_ui('root')
        input = AppUI().get_input('root')
        if input == '1': 
            AppQlontong().catat_penjualan()
            
        elif input == 2:
            print("2")

transaksi_df = pd.read_csv('transaksi.csv')
barang_df = pd.read_csv('barang.csv')
AppQlontong(transaksi_df, barang_df).main_page()
