from sqlalchemy.orm import Session
from models import PolicyTypeModel, PolicyModel
from utils.logger import get_logger
from datetime import date
from slugify import slugify

logger = get_logger("seeds.policies")

def seed_policies(db: Session) -> dict:
    """
    Seed policy types and policies.
    
    Args:
        db: Database session
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Define policy types
        policy_types_data = [
            {
                "name": "Terms of Use",
                "description": "Terms and conditions governing the use of Career Elevate services",
                "is_required": True
            },
            {
                "name": "Privacy Policy",
                "description": "Privacy policy explaining how we collect, use, and protect personal data",
                "is_required": True
            }
        ]
        
        # Define policy content
        terms_of_use_content = """<section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">1. Our Mission</h3>
                        <p>
                            At CareerElevate.ai, our mission is to empower ambitious professionals to succeed in global
                            interviews by
                            mastering English with clarity, confidence, and impact. We combine AI-powered coaching with
                            proven
                            communication frameworks to help you sharpen your answers, refine your executive presence,
                            and showcase
                            your value with authority. Our focus is not on perfection, but on performance — enabling you
                            to
                            communicate strategically, connect authentically, and stand out in high-stakes international
                            interviews.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">2. Eligibility</h3>
                        <p>
                            You may use our Services only if you are at least 18 years old, or of legal age in your
                            jurisdiction, and
                            capable of entering into binding agreements.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">3. Account Registration &amp; Security</h3>
                        <p>
                            You must provide accurate information when registering, keep your credentials secure, and
                            notify us of
                            unauthorized use. Accounts cannot be shared without permission.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">4. Scope of Services</h3>
                        <p>
                            Our Services include AI-powered coaching, optional live coaching sessions, and learning
                            content. We
                            provide tools to support your preparation but do not guarantee employment or outcomes.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">5. Payments, Subscriptions &amp; Refunds</h3>
                        <p>Subscription fees are billed in advance. All prices are listed in EUR and include VAT where
                            applicable.</p>
                        <p>
                            EU and French users have a 14-day right of withdrawal for online purchases. However, this
                            right does not
                            apply once digital content is made available to you, provided you have given your express
                            consent and
                            acknowledgment that you waive your right of withdrawal. By purchasing our digital training
                            modules, you
                            agree to immediate access and expressly waive your statutory withdrawal right.
                        </p>
                        <p>
                            Refunds are only given where legally required. Unless otherwise stated, payments are
                            non-refundable once
                            digital services are accessed.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">6. User Responsibilities</h3>
                        <p>
                            You may not misuse our Services, attempt to reverse engineer our platform, or violate
                            applicable laws. You
                            agree not to copy, distribute, resell, or otherwise exploit our content or platform for
                            commercial
                            purposes without written authorization.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">7. Intellectual Property</h3>
                        <p>
                            All platform software, branding, and content belong to CareerElevate.ai or its licensors.
                            You are granted
                            a limited, non-exclusive, non-transferable license to use the Services for personal,
                            non-commercial
                            purposes.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">8. Third-Party Services</h3>
                        <p>
                            We may integrate with third-party tools or links. We are not responsible for their services,
                            terms, or
                            data practices. Your use of third-party services is subject to their own terms and policies.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">9. Disclaimers</h3>
                        <p>
                            Our Services are provided 'as is' without guarantees of employment, promotion, or specific
                            outcomes.To the fullest extent permitted by law, we disclaim all warranties, express or
                            implied, including
                            merchantability and fitness for a particular purpose.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">10. Limitation of Liability</h3>
                        <p>
                            We are not liable for indirect, incidental, or consequential damages, including lost
                            opportunities or
                            income.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">11. Indemnification</h3>
                        <p>
                            You agree to indemnify and hold CareerElevate.ai harmless from claims arising from your
                            misuse of the
                            Services.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">12. Governing Law &amp; Jurisdiction</h3>
                        <p>
                            These Terms apply globally, with emphasis on French law and EU consumer and data protection
                            regulations.
                            Disputes will be subject to French courts, unless local law provides otherwise.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">13. Termination</h3>
                        <p>
                            We may suspend or terminate your account if you violate these Terms. You may stop using our
                            Services at
                            any time. Upon termination, your right to access the Services will end, but sections related
                            to
                            intellectual property, liability, and dispute resolution will continue to apply.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">14. Updates to Terms</h3>
                        <p>
                            We may update these Terms from time to time and will notify you of material
                            changes.Continued use of the
                            Services after updates constitutes acceptance of the new Terms.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">15. Miscellaneous</h3>
                        <p>
                            These Terms constitute the entire agreement. If any provision is invalid, others remain
                            effective. Failure
                            to enforce is not a waiver. These Terms do not create any partnership, joint venture, or
                            employment
                            relationship between you and CareerElevate.ai.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">16. Contact Us</h3>
                        <p>
                            For questions, contact us at hello@careerelevate.ai | Website: www.careerelevate.ai |
                        </p>
                    </section>

                <section aria-labelledby="refund-en" class="space-y-6">
                    <header>
                        <h2 id="refund-en" class="text-2xl font-bold text-slate-900">Refund Policy</h2>
                        <p class="text-sm text-slate-500">Last Updated: September 2025</p>
                    </header>

                    <p>
                        At Career Elevate, we provide premium digital training modules and resources to help ambitious
                        professionals
                        succeed in global interviews.
                    </p>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">1. EU and French Consumer Rights</h3>
                        <p>
                            Under EU and French consumer law, online purchases normally include a 14-day right of
                            withdrawal. However,
                            this right does not apply once digital content is made available to you, provided that:
                        </p>
                        <ul class="list-disc pl-6 space-y-1">
                            <li>you have given your express consent to immediate access, and</li>
                            <li>you have acknowledged that doing so waives your right of withdrawal.</li>
                        </ul>
                        <p>
                            For this reason, during checkout you will be asked to tick a box confirming that you agree
                            to immediate
                            access and that you waive your 14-day right of withdrawal.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">2. Non-Refundable Purchases</h3>
                        <p>
                            Because our products are digital and accessible immediately after purchase, all sales are
                            final and
                            non-refundable once access is granted, unless otherwise required by law.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">3. Exceptions</h3>
                        <p>
                            Refunds may still be granted where required under applicable law, for example in cases of
                            technical
                            failure preventing delivery of the product.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">4. Contact Us</h3>
                        <p>
                            If you have any questions about this Refund Policy, you can contact us at:
                        </p>
                        <p>
                            Career Elevate<br />
                            Email: hello@careerelevate.ai<br />
                            Website: www.careerelevate.ai
                        </p>
                    </section>
                </section>

                <section aria-labelledby="refund-fr" class="space-y-6">
                    <header>
                        <h2 id="refund-fr" class="text-2xl font-bold text-slate-900">Politique de Remboursement</h2>
                        <p class="text-sm text-slate-500">Dernière mise à jour : septembre 2025</p>
                    </header>

                    <p>
                        Chez Career Elevate, nous fournissons des modules de formation numérique premium et des
                        ressources destinées
                        à aider les professionnels ambitieux à réussir leurs entretiens à l'international.
                    </p>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">1. Droits des consommateurs en France et dans
                            l'UE</h3>
                        <p>
                            En vertu du droit de la consommation en vigueur dans l'Union européenne et en France, les
                            achats en ligne
                            bénéficient normalement d'un droit de rétractation de 14 jours. Toutefois, ce droit ne
                            s'applique pas dès
                            lors que le contenu numérique est mis à votre disposition, à condition que :
                        </p>
                        <ul class="list-disc pl-6 space-y-1">
                            <li>vous ayez donné votre consentement exprès à un accès immédiat, et</li>
                            <li>vous ayez reconnu que, ce faisant, vous renoncez à votre droit de rétractation.</li>
                        </ul>
                        <p>
                            Pour cette raison, lors du processus d'achat, il vous sera demandé de cocher une case
                            confirmant que vous
                            acceptez l'accès immédiat et que vous renoncez à votre droit de rétractation de 14 jours.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">2. Achats non remboursables</h3>
                        <p>
                            Étant donné que nos produits sont numériques et accessibles immédiatement après l'achat,
                            toutes les ventes
                            sont définitives et non remboursables une fois l'accès accordé, sauf obligation légale
                            contraire.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">3. Exceptions</h3>
                        <p>
                            Des remboursements peuvent néanmoins être accordés lorsqu'ils sont requis par la loi
                            applicable, par
                            exemple en cas de défaillance technique empêchant la livraison du produit.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">4. Contact</h3>
                        <p>
                            Si vous avez des questions concernant cette Politique de Remboursement, vous pouvez nous
                            contacter à :
                        </p>
                        <p>
                            Career Elevate<br />
                            Email : hello@careerelevate.ai<br />
                            Site web : www.careerelevate.ai
                        </p>
                    </section>
                </section>"""
        
        privacy_policy_content = """<section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">1. Introduction</h3>
                        <p>
                            Career Elevate ("we", "us", "our") values your privacy and is committed to protecting your
                            personal data in
                            accordance with the General Data Protection Regulation (EU) 2016/679 ("GDPR") and the French
                            Data Protection
                            Act (Loi Informatique et Libertés, as amended). This Privacy Policy explains what personal
                            data we collect,
                            how we use it, how we protect it, with whom we may share it, and the rights you have under
                            applicable data
                            protection laws. By using our website, services, or related platforms ("Services"), you
                            agree to the
                            practices described in this Privacy Policy.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">2. What Personal Data We Collect</h3>
                        <p>
                            "Personal Data" means any information relating to an identified or identifiable individual
                            (such as name,
                            email address, identification number, or online identifier). When you use our Services, we
                            may collect and
                            store the following personal information:
                        </p>
                        <ul class="list-disc pl-6 space-y-1">
                            <li>First Name</li>
                            <li>Middle Name</li>
                            <li>Last Name</li>
                            <li>Country</li>
                            <li>Email Address</li>
                            <li>Profession</li>
                            <li>Industry</li>
                            <li>Years of Experience</li>
                        </ul>
                        <p>We may also collect certain non-identifiable data automatically through cookies and
                            analytics.</p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">3. Cookies and Similar Technologies</h3>
                        <p>
                            We use cookies and similar technologies to improve your browsing experience and provide
                            tailored services.
                        </p>
                        <p><strong>What are cookies?</strong> Small text files stored on your device that allow us to
                            recognize your browser and remember your preferences.</p>
                        <p><strong>Why we use cookies:</strong> To analyze usage, improve our platform, and provide a
                            personalized experience.</p>
                        <p><strong>Third-party cookies:</strong> Some cookies may be managed by third-party providers.
                            Please refer to their policies for details.</p>
                        <p>You can manage or disable cookies in your browser settings.</p>
                        <p>
                            <strong>Consent:</strong> Where required by law, we will obtain your consent before placing
                            non-essential
                            cookies (e.g., analytics or advertising cookies). You may withdraw consent or manage cookie
                            preferences at
                            any time through our cookie banner or browser settings.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">4. Why We Process Your Personal Data (Lawful
                            Basis)</h3>
                        <p>We process your Personal Data only when we have a lawful basis under the GDPR, including:</p>
                        <ol class="list-decimal pl-6 space-y-1">
                            <li><strong>Performance of a contract</strong> – to provide you with our Services.</li>
                            <li><strong>Legitimate interests</strong> – to improve and secure our Services.</li>
                            <li><strong>Consent</strong> – when you agree to receive communications, participate in
                                surveys, or allow use of cookies.</li>
                            <li><strong>Legal obligation</strong> – where processing is required to comply with
                                applicable laws.</li>
                        </ol>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">5. Purposes of Processing</h3>
                        <p>Your Personal Data may be used for the following purposes:</p>
                        <ul class="list-disc pl-6 space-y-1">
                            <li>To create and manage your Career Elevate profile.</li>
                            <li>To deliver and improve our career development tools and services.</li>
                            <li>To communicate with you about updates, opportunities, or relevant resources.</li>
                            <li>To analyze user activity and improve user experience.</li>
                            <li>To comply with legal and regulatory requirements.</li>
                            <li>For any purpose you have specifically consented to.</li>
                        </ul>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">6. Data Retention</h3>
                        <p>
                            We retain your Personal Data for as long as your account remains active and for up to
                            <strong>3 years</strong> after your last
                            interaction with our Services if you do not reactivate your account, unless a longer period
                            is required by law.
                            Certain data (such as contractual information) may be archived for up to <strong>5
                                years</strong> in line with French legal
                            obligations. Data collected via cookies and trackers is retained for a maximum of <strong>13
                                months</strong>, in accordance with
                            CNIL guidance.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">7. Your Rights Under GDPR</h3>
                        <p>As a data subject under GDPR, you have the right to:</p>
                        <ul class="list-disc pl-6 space-y-1">
                            <li><strong>Access</strong> – request a copy of your personal data.</li>
                            <li><strong>Rectification</strong> – correct inaccurate or incomplete data.</li>
                            <li><strong>Erasure ("Right to be Forgotten")</strong> – request deletion of your data.</li>
                            <li><strong>Restriction of processing</strong> – request limited use of your data.</li>
                            <li><strong>Data portability</strong> – receive your data in a structured, commonly used
                                format.</li>
                            <li><strong>Object</strong> – object to processing based on legitimate interests or for
                                direct marketing.</li>
                            <li><strong>Withdraw consent</strong> – at any time, where processing is based on consent.
                            </li>
                        </ul>
                        <p>
                            To exercise these rights, you may contact us at: <a href="mailto:hello@careerelevate.ai"
                                class="underline">hello@careerelevate.ai</a>.
                            If you are not satisfied with our response, you may lodge a complaint with the <em>CNIL</em>
                            (Commission Nationale de
                            l'Informatique et des Libertés) at
                            <a href="https://www.cnil.fr" target="_blank" rel="noopener"
                                class="underline">www.cnil.fr</a>.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">8. Disclosure of Your Data</h3>
                        <p>We do not sell your personal data. Your information may only be shared with:</p>
                        <ol class="list-decimal pl-6 space-y-1">
                            <li>Trusted service providers who assist us in delivering our Services, under strict
                                confidentiality obligations.</li>
                            <li>Regulatory or legal authorities, where required by law.</li>
                            <li>Affiliates or partners, but only with your prior consent.</li>
                        </ol>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">9. Security Measures</h3>
                        <p>We take appropriate technical and organizational measures to protect your Personal Data,
                            including:</p>
                        <ul class="list-disc pl-6 space-y-1">
                            <li>Encryption of data in transit and at rest.</li>
                            <li>Secure access controls and authentication measures.</li>
                            <li>Role-based access restrictions.</li>
                            <li>Regular monitoring, auditing, and security reviews.</li>
                        </ul>
                        <p>
                            We also require any third-party service providers who process Personal Data on our behalf to
                            implement equivalent
                            levels of security and confidentiality.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">10. International Data Transfers</h3>
                        <p>
                            If your Personal Data is transferred outside the European Economic Area (EEA), we will
                            ensure that adequate safeguards
                            (such as the European Commission's Standard Contractual Clauses) are in place to protect
                            your data. Some of our providers
                            (e.g., analytics, hosting, or email services) may be located in countries outside the EEA,
                            such as the United States. In
                            such cases, we rely on appropriate safeguards, including SCCs or equivalent measures.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">11. Updates to this Privacy Policy</h3>
                        <p>
                            We may update this Privacy Policy to reflect changes in our practices, technology, or legal
                            requirements. Updates will be
                            posted on our website, and where appropriate, communicated directly to you. This Privacy
                            Policy was last updated in
                            September 2025.
                        </p>
                    </section>

                    <section class="space-y-3">
                        <h3 class="text-xl font-semibold text-slate-900">12. Contact Us</h3>
                        <p>
                            Career Elevate<br />
                            Email: <a href="mailto:hello@careerelevate.ai"
                                class="underline">hello@careerelevate.ai</a><br />
                            Website: <a href="https://www.careerelevate.ai" target="_blank" rel="noopener"
                                class="underline">www.careerelevate.ai</a>
                        </p>
                    </section>"""
        
        policy_types_created = 0
        policy_types_skipped = 0
        policies_created = 0
        policies_skipped = 0
        
        # Seed policy types and their policies
        for policy_type_data in policy_types_data:
            # Check if policy type already exists
            existing_type = db.query(PolicyTypeModel).filter(
                PolicyTypeModel.name == policy_type_data["name"]
            ).first()
            
            if existing_type:
                policy_types_skipped += 1
                logger.info(f"Policy type '{policy_type_data['name']}' already exists, skipping")
                policy_type = existing_type
            else:
                # Create policy type
                policy_type = PolicyTypeModel(
                    name=policy_type_data["name"],
                    slug=slugify(policy_type_data["name"]),
                    description=policy_type_data["description"],
                    is_required=policy_type_data["is_required"]
                )
                db.add(policy_type)
                db.commit()
                db.refresh(policy_type)
                policy_types_created += 1
                logger.info(f"Created policy type: {policy_type_data['name']}")
            
            # Check if active policy exists for this type
            existing_policy = db.query(PolicyModel).filter(
                PolicyModel.policy_type_id == policy_type.Id,
                PolicyModel.is_active == True
            ).first()
            
            if existing_policy:
                policies_skipped += 1
                logger.info(f"Active policy for '{policy_type_data['name']}' already exists, skipping")
            else:
                # Determine content based on policy type
                content = terms_of_use_content if policy_type.name == "Terms of Use" else privacy_policy_content
                
                # Create policy
                policy = PolicyModel(
                    title=f"{policy_type.name} - January 2026",
                    version="1.0.0",
                    content=content,
                    effective_date=date(2026, 1, 8),
                    is_active=True,
                    policy_type_id=policy_type.Id
                )
                db.add(policy)
                db.commit()
                db.refresh(policy)
                policies_created += 1
                logger.info(f"Created policy: {policy.title}")
        
        message = f"Policy seeding completed: {policy_types_created} types created, {policy_types_skipped} types skipped, {policies_created} policies created, {policies_skipped} policies skipped"
        logger.info(message)
        
        return {
            "success": True,
            "message": message,
            "policy_types_created": policy_types_created,
            "policy_types_skipped": policy_types_skipped,
            "policies_created": policies_created,
            "policies_skipped": policies_skipped
        }
        
    except Exception as e:
        logger.error(f"Error seeding policies: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "message": f"Error seeding policies: {str(e)}"
        }
