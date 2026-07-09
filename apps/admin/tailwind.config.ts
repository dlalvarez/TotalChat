import type { Config } from 'tailwindcss';
export default { content: ['./index.html','./src/**/*.{ts,tsx}'], theme: { extend: { colors: { brand: {50:'#eef9ff',100:'#d9f0ff',500:'#1877a6',600:'#116187',700:'#0f4f6d',900:'#123446'}, clinic: {50:'#f3fbf8',500:'#1c9a78',600:'#147b60'} }, boxShadow: { soft:'0 18px 45px rgba(15, 79, 109, 0.10)' } } }, plugins: [] } satisfies Config;
