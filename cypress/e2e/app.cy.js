describe('Testare completă aplicație - Skin.AI', () => {

    const baseUrl = 'http://localhost:5001';

    beforeEach(() => {
        cy.visit(`${baseUrl}/login`);
        cy.get('input[name=email]').type('exist@example.com');
        cy.get('input[name=password]').type('parola_corecta');
        cy.get('button[type=submit]').click();
        cy.contains('Logout');
    });

    it('Pagina de Home', () => {
        cy.visit(`${baseUrl}/`);
        cy.contains('Skin. Ai.');
    });

    it('Pagina de produse', () => {
        cy.visit(`${baseUrl}/produse`);
        cy.contains('Produse');
        cy.get('.product-card').should('exist');
    });

    it('Pagina de favorite', () => {
        cy.visit(`${baseUrl}/favorite`);
        cy.contains('Produsele tale favorite');
    });

    it('Pagina de rutină', () => {
        cy.visit(`${baseUrl}/rutina_mea`);
        cy.url().then((url) => {
            if (url.includes('/profile')) {
                cy.contains('Profilul meu');
            } else {
                cy.contains('✨ Rutina personalizată ✨');
            }
        });
    });

    it('Pagina de profil', () => {
        cy.visit(`${baseUrl}/profile`);
        cy.contains('Profilul meu');
    });

    it('Pagina de quiz', () => {
        cy.visit(`${baseUrl}/beauty_quiz`);
        cy.contains('Quiz');
    });

    it('Pagina de analiză a tenului', () => {
        cy.visit(`${baseUrl}/analiza_tenului`);
        cy.contains('Analizează-ți Tipul de Ten');
    });

    it('Upload imagine', () => {
        cy.visit(`${baseUrl}/analiza_tenului`);
        cy.get('input[type=file]').attachFile('test_image.png');

        // Verificăm că apare rezultatul analizei
        cy.contains('Rezultatul Analizei:');

        // Verificăm că apare și textul cu "Tenul tău este: USCAT" sau GRAS sau ACNEIC
        cy.get('.prediction-result').should('contain.text', 'Tenul tău este:');

        // Verificăm că JS-ul a populat titlul carousel-ului (fetch)
        cy.get('#carousel-titlu', { timeout: 10000 })
            .should('contain.text', 'Iată câteva produse recomandate pentru tine');
    });

    it('Logout', () => {
        cy.visit(`${baseUrl}/`);
        cy.contains('Logout').click();
        cy.url().should('eq', `${baseUrl}/`);
        cy.contains('Skin. Ai.');
    });

    // 🔥 TESTE PE API / POST 🔥

    it('Adaugare și ștergere favorite', () => {
        // Adaugare favorite
        cy.request({
            method: 'POST',
            url: `${baseUrl}/toggle_favorite`,
            body: { product_id: 1, action: 'add' },
            headers: { 'Content-Type': 'application/json' }
        }).then((response) => {
            expect(response.status).to.eq(200);
            expect(response.body).to.have.property('success', true);
        });

        // Ștergere favorite
        cy.request({
            method: 'POST',
            url: `${baseUrl}/toggle_favorite`,
            body: { product_id: 1, action: 'remove' },
            headers: { 'Content-Type': 'application/json' }
        }).then((response) => {
            expect(response.status).to.eq(200);
            expect(response.body).to.have.property('success', true);
        });
    });

    it('Adaugare produs în rutina', () => {
        cy.request({
            method: 'POST',
            url: `${baseUrl}/adauga_in_rutina`,
            form: true,
            body: { product_id: '1', product_type: 'cleanser' }
        }).then((response) => {
            expect(response.status).to.eq(200);
        });
    });

    it('Ștergere produs din rutina', () => {
        cy.request({
            method: 'POST',
            url: `${baseUrl}/sterge_din_rutina`,
            form: true,
            body: { product_id: '1' }
        }).then((response) => {
            expect(response.status).to.eq(200);
        });
    });

    it('Actualizare profil', () => {
        cy.request({
            method: 'POST',
            url: `${baseUrl}/profile`,
            form: true,
            body: {
                nume: 'Test User',
                varsta: '25',
                gen: 'feminin',
                tip_ten: 'uscat',
                alergii: 'parfum',
                textura: 'usoara'
            }
        }).then((response) => {
            expect(response.status).to.eq(200);
        });
    });

    it('Submit quiz', () => {
        cy.request({
            method: 'POST',
            url: `${baseUrl}/beauty_quiz`,
            form: true,
            body: {
                piele_dupa_curatare: 'uscata',
                acnee: 'nu',
                preocupare: 'riduri',
                spf: 'da',
                parfum: 'nu'
            }
        }).then((response) => {
            expect(response.status).to.eq(200);
        });
    });

    it('API Căutare produse', () => {
        cy.request({
            method: 'GET',
            url: `${baseUrl}/cautare?query=test`
        }).then((response) => {
            expect(response.status).to.eq(200);
            expect(response.body).to.be.an('array');
        });
    });

});
