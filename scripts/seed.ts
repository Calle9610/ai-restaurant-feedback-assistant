import { createServiceClient } from '../lib/supabase';

const db = createServiceClient();

function rndDate(weeksBack = 8): string {
  const ms = weeksBack * 7 * 24 * 60 * 60 * 1000;
  return new Date(Date.now() - Math.random() * ms).toISOString();
}

type ReviewRow = { rating: 1 | 2 | 3 | 4 | 5; text: string };

// ─── Tennstopet ───────────────────────────────────────────────────────────────
// Profil: Klassisk husmanskrog i Vasastan. Stabilt stark – stammisar och välförtjänt rykte.
// Enstaka klagomål på väntetid och service under rusningstid. Snitt ~4.2.

const tennstopet: ReviewRow[] = [
  { rating: 5, text: "Klassisk stockholmskrog på sitt bästa. Köttbullarna med potatismos är de bästa jag ätit – perfekt kryddade och lagom mäktiga. Personalen kände igen oss och välkomnade oss värmt. Absolut ett återbesök." },
  { rating: 5, text: "Bästa husmanskost i Vasastan, punkt. Lunchen är ett oslagbart erbjudande – soppa, bröd och en öl för ett rimligt pris. Var hittar man det mer?" },
  { rating: 5, text: "Stämningen på fredag kväll är magisk. Musik i lagom volym, gäster i alla åldrar och personal som har kul på jobbet. Maten är traditionell och vällagad." },
  { rating: 5, text: "Gick dit för en enkel middag och fick en minnesvärd kväll. Picklade grönsaker som tilltugg, mört kött och en dessert som smälte i munnen. Stammis från och med nu." },
  { rating: 5, text: "Kolbullarna är en upplevelse utöver det vanliga. Kombinationen med rimmat fläsk och brynt smör är inte från denna värld. Bra ölmeny dessutom." },
  { rating: 5, text: "Personalen är bland de bästa i branschen – genuina råvarusrekommendationer och koll på säsongen. Maten levererar varje gång." },
  { rating: 5, text: "Perfekt ölhantverk bakom bardisken. Hade den lokala lagerölen till min sill – en kombination man inte glömmer." },
  { rating: 5, text: "Riktigt hemlagad känsla. Inget halvfabrikat, allt görs med omsorg. Portionerna är generösa för priset." },
  { rating: 5, text: "Kom hit med hög förväntan och gick därifrån ännu mer imponerad. Wallenbergaren var perfekt rosa inuti. Servitören var kunnig och hade bra humor." },
  { rating: 5, text: "Silluncherna på måndagar är en institution man inte får missa. Klassisk svensk matkultur bevarad i modern tappning." },
  { rating: 5, text: "Varmt välkomnande, fint hantverk och mat som sitter länge i minnet. Tack för en toppenkväll!" },
  { rating: 5, text: "Julbordet här är magiskt. Bokat tre år i rad och aldrig blivit besviken. Snaps, sill och husmanskost som det ska vara." },
  { rating: 5, text: "Rökta rätter är deras specialitet och det märks – otroligt smakrik och balanserad mat. Återkommer definitivt." },
  { rating: 4, text: "God mat och trevlig personal. Vi fick vänta drygt 20 minuter på maten under fredagskvällen, men servitören ursäktade sig. Köttbullarna förtjänar all beröm." },
  { rating: 4, text: "Bra helhetstryck. Menyn är inte superlång men det som finns är bra genomfört. Bordet var lite nära entrén, men annars utmärkt." },
  { rating: 4, text: "Riktigt god fisk i säsong. Trevligt ställe men lite trångt när det är fullt hus – hade svårt att höra varandra." },
  { rating: 4, text: "Fenomenal sill och inlagd gurka. Lätt att fastna i förrätten. Kom ihåg att boka i förväg – det är alltid fullt." },
  { rating: 4, text: "Genomtrevlig lunch. Soppan var lite salt men brödet var fantastiskt. Personal med god energi." },
  { rating: 4, text: "God mat och snabb service under lunchen. Middagen tog däremot längre tid. Lite otydlig service kvällstid." },
  { rating: 4, text: "Bra husmanskost till bra pris. Inget som sticker ut men heller ingen besvikelse. Solidt val för en enkel middag." },
  { rating: 4, text: "Stämde av matsedeln på nätet och den stämde – skönt när inte halva menyn är slut. God mat, lite segt att fånga servitörens uppmärksamhet." },
  { rating: 3, text: "Okej besök, inte mer. Köttbullarna var lite torra i kanten och lingonen verkade vara från burk. Förväntade mig mer av det anrika ryktet." },
  { rating: 3, text: "Bullrigt och trångt på lördag kväll. Svårt att höra sin bordsgranne. Maten var bra men helhetsupplevelsen gick ner ett par snäpp." },
  { rating: 3, text: "Maten var okej men inte den hype man hör. Personalen var lite stressad under rusningen. Kanske bara otur med timingen." },
  { rating: 3, text: "Räkade vara där under ett fotbollsläge – mer sportbar än restaurang i stämningen. Inget fel i sig, men passade inte vår middag." },
  { rating: 3, text: "Mat: 4/5. Service: 2/5. Servitören missade vår beställning och vi fick påminna tre gånger. Förstår inte hur det kan bli så slappt på ett konstant fullt ställe." },
  { rating: 2, text: "Väntade 55 minuter på maten trots halvtomma lokalen, utan att någon informerade oss. Köttbullarna var goda men upplevelsen förstördes av väntetiden." },
  { rating: 2, text: "Fick fel rätt och när vi påpekade det var servitörens ton defensiv. Kompensationen var en liten rabatt. Inte vad man förväntar sig." },
  { rating: 1, text: "Oförskämt bemötande av en av servitörerna. Vi kände oss som besvär från vi satte oss till vi betalade. Maten var genomsnittlig. Går inte dit igen." },
  { rating: 4, text: "Krogen är alltid fullbokad vilket säger allt. Lyckades få ett bord i baren på en torsdag – perfekt spontanbesök." },
];

// ─── Kommendören ─────────────────────────────────────────────────────────────
// Profil: Formell klassisk restaurang på Östermalm. Hög prisnivå skapar höga förväntningar.
// Klagomål på pris/portion och stel service. Maten imponerar när allt stämmer. Snitt ~4.1.

const kommendoren: ReviewRow[] = [
  { rating: 5, text: "En av Stockholms absolut bästa klassiska restauranger. Maten är sofistikerad utan att vara pretentiös. Vinlistan är imponerande och sommelieren är en av de kunnigaste jag mött." },
  { rating: 5, text: "Perfekt för affärsmiddag. Diskret och elegant miljö, mat av högsta klass. Ryggbiffens stekgrad var exakt som beställt – en sällsynthet nuförtiden." },
  { rating: 5, text: "Jubileumsmiddag som inte glöms. Personalen fixade diskret en liten dekoration på bordet. Maten var strålande och vinerna välmatchade." },
  { rating: 5, text: "Bästa viltmenyn i Stockholm höst som höst. Rådjuret smälte i munnen och rödvinssåsen var magnifik. Värt att boka långt i förväg." },
  { rating: 5, text: "Stämningen är tidlöst elegant. Klassisk stockholmsrestaurang med ett hjärta. Maten är traditionell men inte gammalmodig." },
  { rating: 5, text: "God mat, varm personal, vacker lokal. Lite formellt men det tillhör konceptet. Svårt att hitta ett argument för att inte ge fem stjärnor." },
  { rating: 5, text: "Lunchmötet avklarades med bravur tack vare Kommendörens professionalism. Enkel, smakrik lunch och diskret service. Perfekt miljö för affärer." },
  { rating: 5, text: "Ostserveringen är en upplevelse i sig. Kunnig personal som guidar dig rätt. Avslutade en strålande middag på allra bästa sätt." },
  { rating: 5, text: "Suverän matupplevelse. Från amuse-bouche till dessert var allt välkalibrerat. Personalen är lyhörd och genuint kunnig." },
  { rating: 5, text: "Gick dit med låga förväntningar och gick därifrån helt imponerad. Torskrätten var en avslöjning och priset var rimligare än väntat." },
  { rating: 5, text: "Förvånansvärt god mat för priset. Visst är det inte billigt men varje krona sitter på rätt ställe. Entrecôten var fenomenal." },
  { rating: 4, text: "Mycket god mat men servicetempot ojämnt – lång väntan mellan förrätt och huvudrätt. Konversationen fick spela förstafiolen, vilket faktiskt var okej." },
  { rating: 4, text: "Vällagad mat och vackert uppdukat. Lite formellt för min smak men passade sällskapet. Vinrekommendationerna var dock fantastiska." },
  { rating: 4, text: "Solida fyra stjärnor. Ingenting att klaga på egentligen – servicen var proffsig och korrekt men det saknas lite personlighet." },
  { rating: 4, text: "God mat och bra service. Kände mig lite bortkollrad i den stora menyn – önskar att personalen var mer proaktiv med rekommendationer." },
  { rating: 4, text: "Riktigt god torskrätt. Vinlistan är imponerande och välprissatt. Servicen var formell men uppmärksam hela kvällen." },
  { rating: 4, text: "Bra krog med tydlig identitet. Passar inte alla (lite för formellt för fredagspub-stämning) men gör det den gör riktigt bra." },
  { rating: 4, text: "Fantastisk vinterkväll med god mat och bra vinsällskap. Önskar att dessertmenyn var mer spännande och nyskapande." },
  { rating: 4, text: "Bra mat och fin miljö. Fick lite väl länge vänta på att fånga servitörens uppmärksamhet. Annars gott i allt." },
  { rating: 4, text: "Vacker interiör och god mat. Lite kallt i lokalen kvällen vi var där – kom ihåg ett extra lager." },
  { rating: 3, text: "Förväntat mer av ryktet. Maten var god men inget exceptionellt. Prisnivån är hög vilket höjer förväntningarna onödigt mycket." },
  { rating: 3, text: "Lite stel service som fick oss att känna oss iakttagna snarare än välkomnade. Maten var god men saknade personlighet." },
  { rating: 3, text: "God mat men lång väntetid utan information. Vi satt 30 minuter utan kontakt från servitörerna. Borde vara bättre på den här nivån." },
  { rating: 3, text: "Väldigt dyrt för vad man får. Portionsstorlekarna är lite för 'fine dining' för att motivera prisnivån." },
  { rating: 3, text: "Stämningen var lite dämpad kvällen vi besökte. Känslan av att personalen inte riktigt hade lust. Ovanligt för ett ställe av den här kalibern." },
  { rating: 3, text: "Okej mat, lite för konservativt. Ingenting på menyn kändes spännande eller oväntat. Förstår konceptet men det talade inte till mig." },
  { rating: 2, text: "Bokade via appen och fick ett mejl om att bokningen inte gått igenom – men vi dök upp ändå och bordet var ledigt. Märklig kommunikation satte en bitter prägel." },
  { rating: 2, text: "Kände oss ignorerade under hela middagen. Fick fråga om vatten tre gånger. Maten var god men service på den nivån är inte acceptabelt i den priskategorin." },
  { rating: 1, text: "Betalade 2 200 kr per person för en middag som var genomsnittlig. Servitören var arrogant och fick oss att känna oss oönskade. Rekommenderar inte." },
  { rating: 5, text: "Prova kalvfilén! Sältan, stekyta och tillbehören var perfekt balanserade. Sommelier-guidningen var ett lyft för hela kvällen." },
];

// ─── Tako ─────────────────────────────────────────────────────────────────────
// Profil: Japansk-nordisk fusionskrog på Östermalm. Hög kreativitet och hög prisnivå.
// Klagomål på portionsstorlekar och pris. Omakase-upplevelse i toppen. Snitt ~4.1.

const tako: ReviewRow[] = [
  { rating: 5, text: "Bästa sushiupplevelsen i Stockholm. Chefens specialrulle med tryffelriven och wagyu är en sensation. Atmosfären är livlig och bartenderna är riktiga konstnärer." },
  { rating: 5, text: "Fantastisk omakase! Vi satte oss i chefens händer och varje rätt var en avslöjning. Extremt kreativt och välbalanserat utan att bli pretentiöst." },
  { rating: 5, text: "Karaktär och kreativitet i varje rätt. Tataki, crudo och japanska cocktails – något för alla sinnen. Perfekt för en specialkväll." },
  { rating: 5, text: "Imponerande meny med japanska ingredienser och svenska råvaror. Kombinationen var snygg och smakrik. Personalen var engagerad och passionerad." },
  { rating: 5, text: "Gick hit för en date och kvällen var perfekt. Intim miljö, välgjord mat och cocktails som var konstverk. Lite dyrt men värt varje krona." },
  { rating: 5, text: "Spetsat edamamebönor, tartaren med ponzu, laxrullarna – allt satt. Servicen var varm och proaktiv. Bästa besök det här kvartalet." },
  { rating: 5, text: "Drinkmenyn är på en helt annan nivå. Bartenderna mixar cocktails med japanska ingredienser och det funkar perfekt till maten." },
  { rating: 5, text: "Högt under tak och vacker design. Maten är innovativ men tillgänglig. Det grillerade bläckfisket var kvällens klara vinnare." },
  { rating: 5, text: "Fantastisk kväll med vänner. Delade rätter är rätt approach. Vi beställde sju rätter och varje bit var värd att minnas." },
  { rating: 5, text: "Lyckades få bord på en lördagskväll utan bokning – ett litet mirakel. Personalen var flexibla och trevliga. Maten levererade." },
  { rating: 5, text: "Gyozas är de bästa i Stockholm och den stekta risrätten var magisk. Inte det billigaste men pengarna spenderas rätt." },
  { rating: 5, text: "Japansk precision möter nordisk enkelhet i ett av Östermalms mer spännande matrum. Värde för pengarna finns i de lite dyrare rätterna." },
  { rating: 5, text: "Matlagningen är verkligen kreativ utan att kännas sökt. Misosoppan och tempuran var outstanding. Återkommer nästa månad." },
  { rating: 5, text: "Superb omakase! Vi var fyra personer och alla lämnade begeistrade. Kockarnas passion är smittsam och märks i varje rätt." },
  { rating: 4, text: "Riktigt god mat men lite för högt ljud – vi fick skrika till varandra. Perfekt för ett glatt gäng men svårare för en intim middag." },
  { rating: 4, text: "Bra mat och bra drinkar. Väntetiden på maten var ojämn – förrätt kom snabbt sedan dröjde det. Ingenting som förstörde kvällen." },
  { rating: 4, text: "Sushimenyn är stark med råvarukvalitet på topp. Drog ner lite för portionsstorlekarna – fem bitar sushi för 195 kr känns snålt." },
  { rating: 4, text: "Fantastiska smaker men matsalen var överfull och servicen stressad. De borde kanske begränsa antalet gäster per kväll." },
  { rating: 4, text: "Hög smakprofil. Tempura och edamame var outstanding. Önskar att dessertmenyn matchade resten av upplevelsen." },
  { rating: 4, text: "Bra sushirestaurang. Mango-chilisåsen på laxrullarna var unik och smakrik. Lite trängre bord än vi hade önskat." },
  { rating: 4, text: "Innovativ mat och vacker presentation. Lite för trendy för min smak men det är personlig preferens – maten i sig är utmärkt." },
  { rating: 4, text: "God mat och stämning. Fick lite väl länge vänta på uppmärksamhet i baren vid ankomst. Annars en bra kväll." },
  { rating: 4, text: "God mat men servicen var lite robotaktig – känslan av inpluggade repliker snarare än naturliga samtal. Maten i sig är utmärkt." },
  { rating: 3, text: "Portionerna är för små för prisnivån. Betalade 1 400 kr per person och gick hem lite hungrig. Smakerna var bra men värde för pengarna stämmer inte." },
  { rating: 3, text: "Hype-restaurang med halvbra mat. Visst är det kreativt men det kreativa överskuggar smaken i ett par rätter. Dessutom svårt att boka." },
  { rating: 3, text: "Lite för högt ljud för en normal konversation. Maten var okej men inte den upplevelse vi förväntade oss utifrån recensionerna." },
  { rating: 3, text: "Service var lite frånvarande kvällen vi besökte. Fick vänta länge på betalning. Maten var bra men snabbare avslutning hade hjälpt." },
  { rating: 3, text: "Bra koncept, ibland riktigt bra utförande. Men ibland känns det som att kreativiteten går lite för långt och smaken lider." },
  { rating: 2, text: "En sushirätt var undertempererad och när vi påpekade det fick vi 'den ska vara så'. Det är inte acceptabelt när man betalar den här prisnivån." },
  { rating: 1, text: "Bokat bord bekräftades men när vi anlände hade de gett bort det. Erbjöds att vänta 1,5 timme. Gick hem och åt pizza istället. Håller inte måttet." },
];

// ─── Tennstopet Grill ─────────────────────────────────────────────────────────
// Profil: Tydlig uppåtgång. Tidiga reviews visar ojämn stekgrad och trög service.
// Senaste 2 månader märks klar förbättring – ny kökschef och starkare råvaror. Snitt ~4.1.

const tennstopetGrill: ReviewRow[] = [
  { rating: 5, text: "Grillad entrecôte med tryffelsmör – perfekt rosa inuti och fin brynt yta. Märkbar skillnad mot mitt besök för ett par månader sedan. Det som var ojämnt då är nu konsekvent bra." },
  { rating: 5, text: "Ribeye för 395 kr med salladsbuffé och surdegsbröd ingår. Köttet var mört och stekgraden exakt som beställt. Bättre än de flesta steakhouses i stan." },
  { rating: 5, text: "Grillkvällen på torsdagar är ett fynd – live-grillning av hel oxfilé på öppen eld, kallt öl och avslappnad stämning. Bokat redan om." },
  { rating: 5, text: "Porterhouse-biffen delad på två var kvällens höjdpunkt. Rökig, saftig och med en chimichurri som inte smakar ur en flaska. Väl värd priset." },
  { rating: 5, text: "Hamburgarna är kronjuvelen: löst format nötkött, smält cheddar och briochebröd som håller ihop hela vägen. Stockholms bästa grillburgare just nu." },
  { rating: 5, text: "Kyckling med piri piri-marinad var saftig och välkryddad. Gick dit på en tisdag utan bokning – fick bord direkt och strålande mat." },
  { rating: 5, text: "Märker att personalen trivs och det smittar av sig. Kockarna verkar genuint stolta. Grillad lax med spenat och kapris – enkelt och perfekt." },
  { rating: 5, text: "Kvällens special – viltfilé med rostad vitlök och hjortrongelé – var mästerlig. Kocken kom ut och frågade hur vi hade det. Det är service." },
  { rating: 5, text: "Ny stamgäst! Grillad majskyckling med lime och jalapeño är en av de bästa kycklingrätterna jag ätit i stockholm. Dröjer inte med återbesöket." },
  { rating: 4, text: "Bra grillkrog med hög nivå på råvarorna. Köttet var saftigt och portionerna generösa. Drog ett snäpp för att dessertmenyn är lite tunn." },
  { rating: 4, text: "God mat och avslappnad stämning. Biffen var bra men stekgraden missades – beställde medium, fick medium well. Inget drama men värt att notera." },
  { rating: 4, text: "Ribeye var utmärkt. Ugnsrostad potatis var perfekt men bearnaisesåsen lite trådig. Bra helhet ändå – återkommer gärna." },
  { rating: 4, text: "Snabb service och vällagad mat. Lite stökigt att fånga servitörens uppmärksamhet i baren, men väl kontaktad var det smidigt och vänligt." },
  { rating: 4, text: "Bra grillburgare med genomtänkta tillbehör. Picklade rödlökar och kålslaw var ett lyft. Boka i förväg – det fylls snabbt nu för tiden." },
  { rating: 4, text: "Ny krog med potential som faktiskt realiseras. Köttvaliteten är hög och det märks. Lite väntan på desserter men ingenting störande." },
  { rating: 4, text: "Genomtrevlig fredagskväll med kollegor. Alla fyra vid bordet var nöjda – ovanligt bra i ett sällskap med olika preferenser. Bra ölsortiment." },
  { rating: 4, text: "Rökig chipotle-marinad på kycklingen var en smakbomb. Enkelt men perfekt genomfört. Bokar inför nästa lönedag." },
  { rating: 3, text: "Ojämnt besök. Kollegans biff var perfekt, min var tuff trots medium-beställning. Lotteri ännu – hoppas det jämnar ut sig." },
  { rating: 3, text: "Väntetiden var 40 minuter på en tisdag med halvtomt hus. Svårt att förstå. Maten var bra men väntan sänkte upplevelsen märkbart." },
  { rating: 3, text: "Priset är okej men portionerna lite snåla. Fick beställa extra tillbehör för att bli mätt – addera det och prisnivån känns hög." },
  { rating: 3, text: "Bra stekyta men köttet var lite grumligt i mitten – undrar om grilltempen inte var rätt. Servitören var hjälpsam och erbjöd alternativ." },
  { rating: 3, text: "Menyn är lite för spretig för en grillkrog. Gå all-in på kött – eller minska och skärp till det ni redan gör bra." },
  { rating: 2, text: "Fick välstekt biff när jag beställde medium rare. Tog 20 minuter att få en ny och sällskapet hade då ätit klart. Färgade hela kvällen negativt." },
  { rating: 2, text: "Besöket för tre månader sedan var riktigt dåligt – segt kött och frånvarande service. Hör att det blivit bättre men det gamla besöket sitter kvar." },
  { rating: 5, text: "Spontanbesök på en fredag, fick bord i baren. Grill-ribeye var kvällens bästa nyhet. Snabb och varm service, bra humör bakom bardisken." },
  { rating: 4, text: "Gick med jobbarkompisar och alla lämnade nöjda. Mat kom snabbt för att vara grillrätt. Köttvaliteten var hög och priset rimligt för centrumlägena." },
  { rating: 4, text: "Märker att de hittat sin rytm nu. Personal verkar trivas och det märks i tempot. Hamburgaren var solid – inte revolutionerande men pålitlig." },
];

// ─── Kapten Jack ─────────────────────────────────────────────────────────────
// Profil: Kämpar med pulled pork-burgaren – torr, brödet smular sönder, tre gäster V23
// nämner exakt samma rätt. Stämning/bar är stark, fisken utmärkt. Snitt ~3.8.

const kaptenJack: ReviewRow[] = [
  { rating: 5, text: "Bästa sjömatstallriken i Stockholm. Ostron, räkor och hummer i perfekt kondition. Havsutblick och nautisk inredning – en upplevelse från start till slut." },
  { rating: 5, text: "Fish and chips var fantastisk – frasig smet, genomstekt och med hemgjord remouladsås. Bästa versionen jag hittat i stan. Återkommer definitivt." },
  { rating: 5, text: "Sjöfartstema genomfört med stil ned till detaljerna. Stämningen på fredagskvällar är fantastisk och bartenderna blandade drinkar som var rena konstverk." },
  { rating: 5, text: "Tigerräkan med chili och vitlök – en av de enklaste och bästa rätterna i Stockholm. Varför gör inte fler krogar det så rätt och så enkelt?" },
  { rating: 5, text: "Underbara uteservering och fantastisk sommarkväll. Sjömats-brickan med ostron, räkor och hummer var fenomenal. Varm och engagerad personal." },
  { rating: 5, text: "Räksalladssmörgåset var en upplevelse. Riklig räkmängd, bra crème fraîche och dill – inte ens det dyraste stället i stan matchar det." },
  { rating: 5, text: "Bra ölsortiment och lättsam stämning. Afterwork som sträckte sig till midnatt utan att vi märkte av det. Personalen höll humöret högt." },
  { rating: 5, text: "Ny favorit för sjömat på Norrmalm. Grillad hummer var perfekt – smörig och söt med fin rökig ton. Servicen var engagerad hela kvällen." },
  { rating: 4, text: "God stämning och bra personal. Ölet är kalt och serverat snabbt. Håll dig till fisksidan av menyn – det är där de verkligen levererar." },
  { rating: 4, text: "Skaldjursbrickan för två var generös och välprissatt. Dryckskortet är välsorterat och bartenderna vet vad de pratar om." },
  { rating: 4, text: "Bra lunch med kollegor. Fisksoppan var värmande och prisvärd. Servicetemperaturen var lite ojämn men ingen stor grej – totalt en bra upplevelse." },
  { rating: 4, text: "Gott läge och trevlig personal. Afterwork-erbjudandet på dryck är bra. Fiskrätterna håller hög klass – undviker burgarna sedan senast." },
  { rating: 4, text: "Sjöfarartemat är genomtänkt. Fiskrätterna genuint bra – undvik köttburgarna om du inte är beredd på besvikelse. Bra ölsortiment." },
  { rating: 4, text: "God Bloody Mary till brunch och utmärkt fish and chips – perfekt krispig och genomstekt. Kompisen som tog burgaren var tydligt besviken." },
  { rating: 4, text: "Bra krog med klar identitet i sina bästa stunder. Väljer man rätt från menyn (fisk och skaldjur) är kvällen utmärkt. Atmosfären är alltid topp." },
  { rating: 3, text: "Pulled pork-burgaren var torr och brödet smulade sönder vid första tuggan. 175 kr för det är för mycket. Kompisen beställde fish and chips – var däremot riktigt bra." },
  { rating: 3, text: "Besökte med jobbet V23. Pulled pork för tre av oss – alla fick exakt samma kommentar: torrt kött och bröd som inte håller ihop. Verkar vara ett strukturproblem i köket." },
  { rating: 3, text: "Stämningen är topp men maten är inkonsekvent. Burgarna behöver ses över – servitören verkade inte förvånad när vi klagade, vilket säger allt om hur känt problemet är." },
  { rating: 3, text: "Bra bar men trögt kök. Fick vänta 35 minuter på en burger på tisdag med halvtomt hus. Stämningen är bästa argumentet för att komma hit." },
  { rating: 3, text: "Ölet är bra och atmosfären är rätt. Pulled pork-burgaren är däremot en besvikelse – torrt kött och smuligt bröd. Fisken är restaurangens egentliga styrka." },
  { rating: 3, text: "Blandat intryck – två tog fisk (utmärkt), en tog burgare (medelmåttigt). Satsa på det ni är bra på och skippa burgarkoncept som inte håller." },
  { rating: 3, text: "Bra pubstämning men lite för högt ljud för en normal middagskonversation. Maten är ojämn – fisken bra, kötträtterna sviker." },
  { rating: 2, text: "Pulled pork-burgaren var urusel – torrt kött, bröd som föll isär och kalla pommes. Betalde 175 kr. Servitören verkade van vid klagomålet. Känt problem som inte åtgärdats." },
  { rating: 2, text: "Tredje gången jag försöker med burgarna och tredje gången besviken. Sista gången. Fish and chips är bra men det räcker inte för att motivera ett återbesök." },
  { rating: 2, text: "Servicefel – fick inte det vi beställde. Tog lång tid att rätta till och ingen ursäkt från personalen. Förvånande för ett ställe med så bra rykte för sin stämning." },
  { rating: 1, text: "En av de sämsta burgers jag ätit i Stockholm. Torrt kött, smuligt bröd, kalla tillbehör – 175 kr är ett skämt. Gå dit för ölet och fisken, inte kötträtterna." },
  { rating: 4, text: "Fantastisk terrass och vällagad fisk. Inredningen är charmig och bartendern bjöd spontant på en smakbitsrunda. Bra minne – och bra argument för att komma tillbaka." },
  { rating: 5, text: "Räksoppa och skaldjursbricka – enkelt och perfekt. Personalen är varm och välkomnande. Krogen vet vad det är bra på när det håller sig till havet." },
];

// ─── Restaurang-definitioner ──────────────────────────────────────────────────

const restaurantDefs = [
  { name: 'Tennstopet',       area: 'Vasastan'  },
  { name: 'Kommendören',      area: 'Östermalm' },
  { name: 'Tako',             area: 'Östermalm' },
  { name: 'Tennstopet Grill', area: 'Vasastan'  },
  { name: 'Kapten Jack',      area: 'Norrmalm'  },
];

// ─── Seed ─────────────────────────────────────────────────────────────────────

async function seed() {
  // Säkerställ att alla restauranger finns i databasen
  console.log('Hämtar befintliga restauranger…');
  const { data: existing } = await db.from('restaurants').select('name');
  const existingNames = new Set((existing ?? []).map((r: { name: string }) => r.name));

  const missing = restaurantDefs.filter((r) => !existingNames.has(r.name));
  if (missing.length > 0) {
    console.log(`Lägger till ${missing.length} ny(a) restaurang(er): ${missing.map((r) => r.name).join(', ')}`);
    const { error } = await db.from('restaurants').insert(missing);
    if (error) { console.error('Kunde inte skapa restauranger:', error); process.exit(1); }
  }

  const { data: restaurants, error: rErr } = await db
    .from('restaurants')
    .select('id, name');

  if (rErr || !restaurants?.length) {
    console.error('Kunde inte hämta restauranger.');
    process.exit(1);
  }

  const byName: Record<string, string> = Object.fromEntries(
    restaurants.map((r: { name: string; id: string }) => [r.name, r.id])
  );

  function requireId(name: string): string {
    const id = byName[name];
    if (!id) throw new Error(`Restaurang "${name}" saknas i databasen`);
    return id;
  }

  console.log('Rensar befintliga omdömen…');
  await db.from('review_analysis').delete().not('review_id', 'is', null);
  const { error: delErr } = await db.from('reviews').delete().not('id', 'is', null);
  if (delErr) { console.error(delErr); process.exit(1); }

  const rows = [
    ...tennstopet.map((r)      => ({ ...r, restaurant_id: requireId('Tennstopet'),       source: 'maîtres', created_at: rndDate() })),
    ...kommendoren.map((r)     => ({ ...r, restaurant_id: requireId('Kommendören'),      source: 'maîtres', created_at: rndDate() })),
    ...tako.map((r)            => ({ ...r, restaurant_id: requireId('Tako'),             source: 'maîtres', created_at: rndDate() })),
    ...tennstopetGrill.map((r) => ({ ...r, restaurant_id: requireId('Tennstopet Grill'), source: 'maîtres', created_at: rndDate() })),
    ...kaptenJack.map((r)      => ({ ...r, restaurant_id: requireId('Kapten Jack'),      source: 'maîtres', created_at: rndDate() })),
  ];

  const { error: insErr } = await db.from('reviews').insert(rows);
  if (insErr) { console.error(insErr); process.exit(1); }

  console.log(`\n✓ Seedade ${rows.length} omdömen totalt:`);
  console.log(`  Tennstopet:       ${tennstopet.length} omdömen`);
  console.log(`  Kommendören:      ${kommendoren.length} omdömen`);
  console.log(`  Tako:             ${tako.length} omdömen`);
  console.log(`  Tennstopet Grill: ${tennstopetGrill.length} omdömen  (profil: uppåtgång)`);
  console.log(`  Kapten Jack:      ${kaptenJack.length} omdömen  (profil: kämpar med burgarna)`);
}

seed();
