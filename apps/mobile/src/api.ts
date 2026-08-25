import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

export type Category = { id: number; name: string; slug: string; description: string };
export type Variant = { id: number; name: string; sku: string; attributes: Record<string,string>; price_cents: number; display_price_cents: number; display_currency: string; stock: number; is_available: boolean };
export type Product = { id:number; name:string; slug:string; brand:string; sku:string; description:string; price_cents:number; display_price_cents:number; currency:string; display_currency:string; stock:number; image_url:string; images:{id:number;url:string;alt_text:string}[]; variants:Variant[]; has_variants:boolean; is_available:boolean; average_rating:number; review_count:number; category:Category };
export type User = { id:number; username:string; email:string; first_name:string; last_name:string; full_name:string; phone:string };
export type Address = { id:number; label:string; full_name:string; phone:string; country_code:string; city:string; region:string; postal_code:string; line1:string; line2:string; is_default:boolean };
export type CartItem = { id:number; product:Product; variant:Variant|null; quantity:number; line_total_cents:number };
export type Cart = { id:number; items:CartItem[]; item_count:number; subtotal_cents:number; discount_cents:number; tax_cents:number; shipping_cents:number; total_cents:number; currency:string; coupon_code:string };
export type Payment = { public_id:string; status:string; amount_cents:number; currency:string; provider:string };
export type Order = { public_id:string; invoice_number:string; status:string; payment_status:string; payment_method:string; full_name:string; phone:string; city:string; address:string; currency:string; subtotal_cents:number; discount_cents:number; tax_cents:number; shipping_cents:number; total_cents:number; items:{id:number;product_name:string;variant_name:string;quantity:number;line_total_cents:number}[]; shipment:null|{tracking_number:string;status:string;estimated_delivery_at:string|null}; latest_payment:Payment|null; created_at:string };
export type Notification = { id:number; title:string; body:string; is_read:boolean; created_at:string };
type Paginated<T> = { count:number; next:string|null; previous:string|null; results:T[] };

const localApiUrl = Platform.select({ android:'http://10.0.2.2:8000/api/v1', ios:'http://127.0.0.1:8000/api/v1', default:'http://127.0.0.1:8000/api/v1' });
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? localApiUrl;
const ACCESS_KEY = 'nova_access_token'; const REFRESH_KEY = 'nova_refresh_token';

async function tokens() { return { access: await SecureStore.getItemAsync(ACCESS_KEY), refresh: await SecureStore.getItemAsync(REFRESH_KEY) }; }
async function saveTokens(access:string, refresh?:string) { await SecureStore.setItemAsync(ACCESS_KEY,access); if(refresh) await SecureStore.setItemAsync(REFRESH_KEY,refresh); }
export async function logout() { await Promise.all([SecureStore.deleteItemAsync(ACCESS_KEY),SecureStore.deleteItemAsync(REFRESH_KEY)]); }

export class ApiError extends Error { constructor(public status:number, public payload:unknown){ super(typeof payload==='object'&&payload&&'detail' in payload?String(payload.detail):'تعذر إكمال الطلب'); } }
export function errorMessage(error:unknown){ if(error instanceof ApiError&&typeof error.payload==='object'&&error.payload)return Object.values(error.payload as Record<string,unknown>).flat().join(' '); return error instanceof Error?error.message:'حدث خطأ غير متوقع'; }

async function refreshAccess(refresh:string){ const response=await fetch(`${API_URL}/auth/token/refresh/`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh})}); if(!response.ok){await logout();return null;} const payload=await response.json() as {access:string;refresh?:string};await saveTokens(payload.access,payload.refresh);return payload.access; }

export async function apiRequest<T>(path:string, init?:RequestInit, retry=true):Promise<T>{
  const stored=await tokens(); const headers:Record<string,string>={Accept:'application/json',...(init?.body?{'Content-Type':'application/json'}:{})};
  if(stored.access)headers.Authorization=`Bearer ${stored.access}`;
  const response=await fetch(`${API_URL}${path}`,{...init,headers:{...headers,...(init?.headers as Record<string,string>|undefined)}});
  if(response.status===401&&stored.refresh&&retry){const access=await refreshAccess(stored.refresh);if(access)return apiRequest<T>(path,init,false);}
  const text=await response.text();const payload=text?JSON.parse(text):null;if(!response.ok)throw new ApiError(response.status,payload);return payload as T;
}

export async function login(username:string,password:string){const payload=await apiRequest<{access:string;refresh:string}>('/auth/token/',{method:'POST',body:JSON.stringify({username,password})},false);await saveTokens(payload.access,payload.refresh);return getMe();}
export async function register(data:Record<string,string>){await apiRequest('/auth/register/',{method:'POST',body:JSON.stringify(data)},false);return login(data.username,data.password);}
export const getMe=()=>apiRequest<User>('/auth/me/');
export const getCategories=()=>apiRequest<Category[]>('/categories/');
export const getProducts=async(query='',category='',currency='SAR')=>{const params=new URLSearchParams({currency});if(query)params.set('q',query);if(category)params.set('category',category);return (await apiRequest<Paginated<Product>>(`/products/?${params}`)).results;};
export const getProduct=(slug:string,currency='SAR')=>apiRequest<Product>(`/products/${slug}/?currency=${currency}`);
export const getFavorites=async()=>{const payload=await apiRequest<Paginated<{id:number;product:Product}>|{id:number;product:Product}[]>('/favorites/');return Array.isArray(payload)?payload:payload.results;};
export const addFavorite=(productId:number)=>apiRequest('/favorites/',{method:'POST',body:JSON.stringify({product_id:productId})});
export const removeFavorite=(favoriteId:number)=>apiRequest(`/favorites/${favoriteId}/`,{method:'DELETE'});
export const getCart=()=>apiRequest<Cart>('/cart/');
export const addCartItem=(productId:number,quantity=1,variantId?:number|null)=>apiRequest<Cart>('/cart/items/',{method:'POST',body:JSON.stringify({product_id:productId,quantity,...(variantId?{variant_id:variantId}:{})})});
export const updateCartItem=(itemId:number,quantity:number)=>apiRequest<Cart>(`/cart/items/${itemId}/`,{method:'PATCH',body:JSON.stringify({quantity})});
export const deleteCartItem=(itemId:number)=>apiRequest(`/cart/items/${itemId}/`,{method:'DELETE'});
export const applyCoupon=(code:string)=>apiRequest<Cart>('/cart/coupon/',{method:'POST',body:JSON.stringify({code})});
export const getAddresses=async()=>{const payload=await apiRequest<Paginated<Address>|Address[]>('/auth/addresses/');return Array.isArray(payload)?payload:payload.results;};
export const createAddress=(data:Record<string,string|boolean>)=>apiRequest<Address>('/auth/addresses/',{method:'POST',body:JSON.stringify(data)});
export const getOrders=async()=> (await apiRequest<Paginated<Order>>('/orders/')).results;
export const getOrder=(id:string)=>apiRequest<Order>(`/orders/${id}/`);
export const createOrder=(addressId:number,paymentMethod:string,currency='SAR')=>apiRequest<Order>('/orders/',{method:'POST',headers:{'Idempotency-Key':`checkout-${Date.now()}-${Math.random().toString(36).slice(2)}`},body:JSON.stringify({address_id:addressId,payment_method:paymentMethod,currency})});
export const initiatePayment=(orderId:string)=>apiRequest<Payment>(`/orders/${orderId}/initiate_payment/`,{method:'POST',headers:{'Idempotency-Key':`${orderId}-${Date.now()}`},body:JSON.stringify({})});
export const confirmPayment=(paymentId:string)=>apiRequest<Payment>(`/payments/${paymentId}/sandbox_confirm/`,{method:'POST',body:JSON.stringify({})});
export const cancelOrder=(orderId:string)=>apiRequest<Order>(`/orders/${orderId}/cancel/`,{method:'POST',body:JSON.stringify({})});
export const requestReturn=(orderId:string,reason:string)=>apiRequest('/returns/',{method:'POST',body:JSON.stringify({order_id:orderId,reason})});
export const getNotifications=async()=> (await apiRequest<Paginated<Notification>>('/notifications/')).results;

export function formatMoney(cents:number,currency='SAR'){return new Intl.NumberFormat('ar-SA',{style:'currency',currency,maximumFractionDigits:2}).format(cents/100);}
