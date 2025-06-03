import { NextResponse } from 'next/server';
import { MailerSend, EmailParams, Recipient } from 'mailersend';

const mailerSend = new MailerSend({
  apiKey: process.env.MAILERSEND_API_KEY || '',
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { recipientEmail, recipientName, senderName, planLink } = body;

    if (!recipientEmail || !planLink) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    const sentFrom = {
      email: process.env.MAILERSEND_FROM_EMAIL || 'noreply@fortana.app',
      name: senderName || 'Fortana Money Planner',
    };

    const recipients = [
      new Recipient(recipientEmail, recipientName || 'Friend')
    ];

    const emailParams = new EmailParams()
      .setFrom(sentFrom)
      .setTo(recipients)
      .setSubject('Money Plan Shared With You')
      .setHtml(`
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #4F46E5;">Money Plan Shared With You</h2>
          <p>Hello${recipientName ? ' ' + recipientName : ''},</p>
          <p>${senderName || 'Someone'} has shared a Money Plan with you.</p>
          <p>You can view the plan by clicking the button below:</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="${planLink}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
              View Money Plan
            </a>
          </div>
          <p style="color: #6B7280; font-size: 14px;">This link will expire in 14 days.</p>
          <p style="color: #6B7280; font-size: 12px; margin-top: 40px; border-top: 1px solid #E5E7EB; padding-top: 20px;">
            This email was sent from Money Plan App. If you didn't expect this email, you can safely ignore it.
          </p>
        </div>
      `)
      .setText(`
        Money Plan Shared With You
        
        Hello${recipientName ? ' ' + recipientName : ''},
        
        ${senderName || 'Someone'} has shared a Money Plan with you.
        
        You can view the plan using this link: ${planLink}
        
        This link will expire in 14 days.
      `);

    const response = await mailerSend.email.send(emailParams);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Email sending error:', error);
    return NextResponse.json(
      { error: 'Failed to send email' },
      { status: 500 }
    );
  }
} 