import { z } from 'zod';

export const loginSchema = z.object({
	email: z.string().email('Invalid email address'),
	password: z.string().min(8, 'Password must be at least 8 characters'),
});

export const registerSchema = z.object({
	full_name: z.string().min(2, 'Name must be at least 2 characters').optional(),
	email: z.string().email('Invalid email address'),
	password: z
		.string()
		.min(8, 'Password must be at least 8 characters')
		.regex(/[A-Z]/, 'Must contain at least one uppercase letter')
		.regex(/[0-9]/, 'Must contain at least one number'),
	confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
	message: 'Passwords do not match',
	path: ['confirm_password'],
});

export const forgotPasswordSchema = z.object({
	email: z.string().email('Invalid email address'),
});

export const resetPasswordSchema = z.object({
	password: z.string().min(8, 'Password must be at least 8 characters'),
	confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
	message: 'Passwords do not match',
	path: ['confirm_password'],
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
