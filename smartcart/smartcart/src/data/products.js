
const products = [
  // =========================
  // ELECTRONICS — 10 PRODUCTS
  // =========================

  {
    id: 1,
    name: "Wireless Headphones",
    category: "Electronics",
    price: 2500,
    image:
      "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 2,
    name: "Smart Watch",
    category: "Electronics",
    price: 3500,
    image:
      "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 3,
    name: "Bluetooth Speaker",
    category: "Electronics",
    price: 2200,
    image:
      "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 4,
    name: "Wireless Mouse",
    category: "Electronics",
    price: 1200,
    image:
      "https://images.unsplash.com/photo-1527814050087-3793815479db?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 5,
    name: "Mechanical Keyboard",
    category: "Electronics",
    price: 4500,
    image:
      "https://images.unsplash.com/photo-1587829741301-dc798b83add3?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 6,
    name: "Power Bank",
    category: "Electronics",
    price: 1800,
    image:
      "https://images.unsplash.com/photo-1609592424948-2d1f8c7d7a25?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 7,
    name: "USB-C Charger",
    category: "Electronics",
    price: 1400,
    image:
      "https://images.unsplash.com/photo-1591290619762-c588f5f3c9f1?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 8,
    name: "Laptop Stand",
    category: "Electronics",
    price: 2000,
    image:
      "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 9,
    name: "Webcam",
    category: "Electronics",
    price: 3200,
    image:
      "https://images.unsplash.com/photo-1587825140708-dfaf72ae4b04?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 10,
    name: "Wireless Earbuds",
    category: "Electronics",
    price: 2800,
    image:
      "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?auto=format&fit=crop&w=600&q=80",
  },

  // =========================
  // FASHION — 10 PRODUCTS
  // =========================

  {
    id: 11,
    name: "Running Shoes",
    category: "Fashion",
    price: 4500,
    image:
      "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 12,
    name: "Classic Backpack",
    category: "Fashion",
    price: 1800,
    image:
      "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 13,
    name: "Casual T-Shirt",
    category: "Fashion",
    price: 900,
    image:
      "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 14,
    name: "Denim Jacket",
    category: "Fashion",
    price: 2800,
    image:
      "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 15,
    name: "Classic Sneakers",
    category: "Fashion",
    price: 3200,
    image:
      "https://images.unsplash.com/photo-1560769629-975ec94e6a86?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 16,
    name: "Leather Wallet",
    category: "Fashion",
    price: 1200,
    image:
      "https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 17,
    name: "Sunglasses",
    category: "Fashion",
    price: 1500,
    image:
      "https://images.unsplash.com/photo-1511499767150-a48a237f0083?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 18,
    name: "Wrist Watch",
    category: "Fashion",
    price: 3800,
    image:
      "https://images.unsplash.com/photo-1524805444758-089113d48a6d?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 19,
    name: "Hoodie",
    category: "Fashion",
    price: 2200,
    image:
      "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 20,
    name: "Canvas Tote Bag",
    category: "Fashion",
    price: 850,
    image:
      "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=600&q=80",
  },

  // =========================
  // HOME — 10 PRODUCTS
  // =========================

  {
    id: 21,
    name: "Coffee Maker",
    category: "Home",
    price: 5500,
    image:
      "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 22,
    name: "Desk Lamp",
    category: "Home",
    price: 1500,
    image:
      "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 23,
    name: "Ceramic Vase",
    category: "Home",
    price: 1200,
    image:
      "https://images.unsplash.com/photo-1581783898377-1c85bf937427?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 24,
    name: "Table Clock",
    category: "Home",
    price: 1000,
    image:
      "https://images.unsplash.com/photo-1563861826100-9cb868fdbe1c?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 25,
    name: "Decorative Plant",
    category: "Home",
    price: 900,
    image:
      "https://images.unsplash.com/photo-1485955900006-10f4d324d411?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 26,
    name: "Throw Pillow",
    category: "Home",
    price: 750,
    image:
      "https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 27,
    name: "Water Bottle",
    category: "Home",
    price: 650,
    image:
      "https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 28,
    name: "Kitchen Organizer",
    category: "Home",
    price: 1300,
    image:
      "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 29,
    name: "Scented Candle",
    category: "Home",
    price: 700,
    image:
      "https://images.unsplash.com/photo-1603006905003-be475563bc59?auto=format&fit=crop&w=600&q=80",
  },
  {
    id: 30,
    name: "Storage Basket",
    category: "Home",
    price: 1100,
    image:
      "https://images.unsplash.com/photo-1593085260707-5377ba37f868?auto=format&fit=crop&w=600&q=80",
  },
];

export default products;

