<script setup>

import { ref, onMounted } from 'vue'
import axios from 'axios'

const products = ref([]) // <--- ตัวแปรนี้ต้องชื่อเดียวกับที่ใช้ใน v-for

const fetchProducts = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/api/products')
    // สำคัญ: ต้องเอา response.data ไปใส่ใน products.value
    products.value = response.data
    console.log("ข้อมูลมาแล้ว:", products.value)
  } catch (error) {
    console.error("ดึงข้อมูลไม่สำเร็จ:", error)
  }
}

// ถ้าไม่มีบรรทัดนี้ ข้อมูลจะไม่โหลดตอนเปิดหน้าเว็บครับ!
onMounted(() => {
  fetchProducts()
})

</script>

<template>
  <div class="min-h-screen bg-[#0f172a] text-slate-200 p-8">
    <div class="max-w-5xl mx-auto">
      <header class="flex justify-between items-center mb-10 border-b border-slate-700 pb-5">
        <h1 class="text-3xl font-black text-cyan-400">MAGIC TALES <span class="text-white">POS</span></h1>
        <div class="text-sm opacity-70">พนักงาน: Chanison</div>
      </header>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="md:col-span-2 grid grid-cols-2 gap-6">
          <div v-for="item in products" :key="item.id"
            class="bg-[#1e293b] rounded-2xl p-4 border border-slate-700 hover:border-cyan-500 transition-all shadow-xl">
            <div class="aspect-video bg-slate-800 rounded-xl mb-4 flex items-center justify-center overflow-hidden">
              <img v-if="item.image" :src="`/images/${item.image}`" class="object-cover w-full h-full"
                @error="(e) => e.target.src = '/images/default-product.png'" />

              <span v-else class="text-slate-500 italic">No Image</span>
            </div>
            <h2 class="text-lg font-bold">{{ item.name }}</h2>
            <p class="text-cyan-400 font-mono text-xl">{{ item.price.toLocaleString() }} THB</p>
            <button class="btn btn-sm btn-outline btn-cyan mt-3 w-full">+ เพิ่มลงตะกร้า</button>
          </div>
        </div>

        <div class="bg-[#1e293b] rounded-3xl p-6 border border-slate-700 h-fit sticky top-8">
          <h3 class="text-xl font-bold mb-6">Order Summary</h3>
          <div class="space-y-4 mb-10">
            <div class="flex justify-between">
              <span class="text-slate-400">Total</span>
              <span class="text-2xl font-bold text-white">0.00 THB</span>
            </div>
          </div>
          <button
            class="btn btn-primary w-full btn-lg bg-cyan-600 border-none hover:bg-cyan-500 text-white shadow-lg shadow-cyan-900/20">
            PAYMENT (QR CODE)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>