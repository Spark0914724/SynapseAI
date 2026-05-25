import api from './client';

export type PlanType = 'free' | 'pro' | 'team';
export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'trialing';

export interface PlanInfo {
	plan: PlanType;
	name: string;
	price_monthly: number;
	tokens_per_month: number;
	features: string[];
	stripe_price_id: string;
}

export interface Subscription {
	id: string;
	user_id: string;
	plan: PlanType;
	status: SubscriptionStatus;
	tokens_used: number;
	tokens_limit: number;
	tokens_remaining: number;
	is_quota_exceeded: boolean;
	stripe_customer_id: string | null;
	stripe_subscription_id: string | null;
}

export const billingApi = {
	getPlans: () =>
		api.get<PlanInfo[]>('/billing/plans'),

	getSubscription: () =>
		api.get<Subscription>('/billing/subscription'),

	createCheckout: (plan: PlanType) =>
		api.post<{ checkout_url: string }>(`/billing/checkout/${plan}`),

	getBillingPortal: () =>
		api.post<{ portal_url: string }>('/billing/portal'),
};
